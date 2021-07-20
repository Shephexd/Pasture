import logging
from typing import List
from collections import defaultdict, OrderedDict
from django.db import DatabaseError, transaction
from neomodel import db
from rest_framework import viewsets
from rest_framework.response import Response
from pasture.assets.models import Asset, DailyPrice, AssetUniverse
from .serializers import AssetSerializer, DailyPriceSerializer, AssetUniverseSerializer
from .filters import DailyPriceFilterSet


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


class DailyPriceViewSet(viewsets.ModelViewSet):
    serializer_class = DailyPriceSerializer
    queryset = DailyPrice.objects.all()
    filterset_class = DailyPriceFilterSet


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
