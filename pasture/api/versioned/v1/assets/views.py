import logging
import pandas as pd
from typing import List, Iterable
from collections import defaultdict, OrderedDict
from neomodel import db
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from pasture.common.viewset import SerializerMapMixin
from pasture.assets.models import Asset, DailyPrice, AssetUniverse
from .serializers import AssetSerializer, SimpleAssetSerializer, DailyPriceSerializer, AssetUniverseSerializer
from .filters import AssetFilterSet, DailyPriceFilterSet, DailyPriceChangesFilterSet


logger = logging.getLogger('pasture')


class AssetViewSet(SerializerMapMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AssetSerializer
    queryset = Asset.objects.all()
    filterset_class = AssetFilterSet
    serializer_class_map = {
        'list': SimpleAssetSerializer
    }
    lookup_field = 'symbol'


class AssetUniverseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AssetUniverse.objects.all()
    serializer_class = AssetUniverseSerializer
    filter_fields = ('universe_id', )


class DailyPriceViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = DailyPriceSerializer
    queryset = DailyPrice.objects.all()
    filterset_class = DailyPriceFilterSet


class DailyPriceChangeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = DailyPriceSerializer
    queryset = DailyPrice.objects.all()
    filterset_class = DailyPriceChangesFilterSet

    def get_pct_changes(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        periods = int(self.request.query_params.get('periods', '1'))
        if page is not None:
            df = self.get_pct_change_df([row.to_dict() for row in page], periods=periods)
            serializer = self.get_serializer([row for i, row in df.iterrows()], many=True)
            return self.get_paginated_response(serializer.data)

        df = self.get_pct_change_df(queryset.values(), periods=periods)
        serializer = self.get_serializer([row for i, row in df.iterrows()], many=True)
        return Response(serializer.data)

    @staticmethod
    def get_pct_change_df(qs: Iterable[DailyPrice], periods: int):
        df = pd.DataFrame(qs)
        df[['open', 'close', 'adj_close', 'high', 'low']] = (df[
            ['open', 'close', 'adj_close', 'high', 'low']].pct_change(periods=periods) + 1).astype(float).cumprod()

        if not df.empty:
            return df.iloc[periods:]
        return df


class AssetNetworkViewSet(viewsets.GenericViewSet):
    queryset = Asset.objects.all()

    def build_tree(self, paths: list, assets: List[str]):
        _cluster_map = defaultdict(list)
        for p in paths:
            _cluster_map[p] += assets
        return _cluster_map

    def list(self, request, *args, **kwargs):
        matched, names = db.cypher_query('MATCH (n)-[r:HAS]->(m:Asset) return n, r, m LIMIT 40')
        cluster_rel = defaultdict(list)

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
