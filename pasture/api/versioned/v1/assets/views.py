import logging
from typing import List
from collections import defaultdict, OrderedDict
from django.db import DatabaseError, transaction
from neomodel import db
from rest_framework import viewsets
from rest_framework.response import Response
from pasture.assets.models import Asset, DailyPrice, AssetUniverse
from .serializers import AssetSerializer, DailyPriceSerializer, AssetUniverseSerializer
from pasture.assets.neomodels import AssetNode, ClusterNode
from linchfin.data_handler.reader import DataReader


logger = logging.getLogger('pasture')


class AssetViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AssetSerializer
    queryset = Asset.objects.all()

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AssetUniverseViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'universe_id'
    queryset = AssetUniverse.objects.all()
    serializer_class = AssetUniverseSerializer

    def filter_queryset(self, queryset):
        return queryset.filter(**self.kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class DailyPriceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DailyPriceSerializer
    queryset = DailyPrice.objects.all()

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        asset_symbols = Asset.objects.all().values_list('symbol', flat=True)
        asset_reader = DataReader()
        ts = asset_reader.get_timeseries(symbols=list(asset_symbols[:5]) + ['BSCF'])

        column_maps = {'Adj Close': 'adj_close', 'Open': 'open', 'Close': 'close',
                       'High': 'high', 'Low': 'low', 'Volume': 'volume', 'Symbols': 'symbol'}

        try:
            with transaction.atomic():
                DailyPrice.objects.filter(symbol__in=ts.Low.columns, created_at__date__in=ts.index)
        except DatabaseError:
            pass

        for i, row in ts.swaplevel(i=-2, j=-1, axis=1).iterrows():
            _daily_price = row.to_frame('value').reset_index().pivot(index='Symbols', columns='Attributes', values='value')
            _daily_price = _daily_price.reset_index().rename(columns=column_maps)
            _daily_price['base_date'] = i.strftime('%Y-%m-%d')
            serializer = DailyPriceSerializer(data=_daily_price.dropna(axis=0).round(2).to_dict(orient='records'), many=True)
            if serializer.is_valid():
                serializer.save()
            else:
                logger.warning(f"{serializer.errors}")
        return super().get_queryset()


class AssetNetworkViewSet(viewsets.GenericViewSet):
    queryset = Asset.objects.all()

    def build_tree(self, paths: list, assets: List[str]):
        _cluster_map = defaultdict(list)
        for p in paths:
            _cluster_map[p] += assets
        return _cluster_map

    def list(self, request, *args, **kwargs):
        print(ClusterNode.nodes.all())
        print(AssetNode.nodes.all())
        matched, names = db.cypher_query('MATCH (n)-[r:HAS]->(m:Asset) return n, r, m')
        cluster_rel = defaultdict(list)
        tree_paths = defaultdict(default_factory=lambda: defaultdict(list))

        for _cluster, r, _asset in matched:
            cluster_name = _cluster._properties['name']
            asset_name = _asset._properties['name']
            cluster_rel[cluster_name].append(asset_name)

        cluster_map = OrderedDict()
        for cluster_name, _assets in cluster_rel.items():
            parent_node, *sub = cluster_name.split('-')
            if parent_node not in cluster_map:
                cluster_map[parent_node] = dict()

            sub_tree = self.build_tree(paths=sub, assets=_assets)
            cluster_map[parent_node].update(sub_tree)
        return Response(cluster_map)
