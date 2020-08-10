# Copyright 2015 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest

import mock

from ._testing import _make_credentials


class TestClusterConstants(object):
    PROJECT = "project"
    INSTANCE_ID = "instance-id"
    LOCATION_ID = "location-id"
    CLUSTER_ID = "cluster-id"
    LOCATION_ID = "location-id"
    CLUSTER_NAME = (
        "projects/" + PROJECT + "/instances/" + INSTANCE_ID + "/clusters/" + CLUSTER_ID
    )
    LOCATION_PATH = "projects/" + PROJECT + "/locations/"
    SERVE_NODES = 5
    OP_ID = 5678
    OP_NAME = "operations/projects/{}/instances/{}/clusters/{}/operations/{}".format(
        PROJECT, INSTANCE_ID, CLUSTER_ID, OP_ID
    )


class MultiCallableStub(object):
    """Stub for the grpc.UnaryUnaryMultiCallable interface."""

    def __init__(self, method, channel_stub):
        self.method = method
        self.channel_stub = channel_stub

    def __call__(self, request, timeout=None, metadata=None, credentials=None):
        self.channel_stub.requests.append((self.method, request))

        return self.channel_stub.responses.pop()


class ChannelStub(object):
    """Stub for the grpc.Channel interface."""

    def __init__(self, responses=[]):
        self.responses = responses
        self.requests = []

    def unary_unary(self, method, request_serializer=None, response_deserializer=None):
        return MultiCallableStub(method, self)


class TestBaseCluster(unittest.TestCase, TestClusterConstants):
    @staticmethod
    def _get_target_class():
        from google.cloud.bigtable.base_cluster import BaseCluster

        return BaseCluster

    def _make_one(self, *args, **kwargs):
        return self._get_target_class()(*args, **kwargs)

    @staticmethod
    def _get_target_client_class():
        from google.cloud.bigtable.client import Client

        return Client

    def _make_client(self, *args, **kwargs):
        return self._get_target_client_class()(*args, **kwargs)

    def test_constructor_defaults(self):
        client = _Client(self.PROJECT)
        instance = _Instance(self.INSTANCE_ID, client)

        cluster = self._make_one(self.CLUSTER_ID, instance)
        self.assertEqual(cluster.cluster_id, self.CLUSTER_ID)
        self.assertIs(cluster._instance, instance)
        self.assertIsNone(cluster.location_id)
        self.assertIsNone(cluster.state)
        self.assertIsNone(cluster.serve_nodes)
        self.assertIsNone(cluster.default_storage_type)

    def test_constructor_non_default(self):
        from google.cloud.bigtable.enums import StorageType
        from google.cloud.bigtable.enums import Cluster

        STATE = Cluster.State.READY
        STORAGE_TYPE_SSD = StorageType.SSD
        client = _Client(self.PROJECT)
        instance = _Instance(self.INSTANCE_ID, client)

        cluster = self._make_one(
            self.CLUSTER_ID,
            instance,
            location_id=self.LOCATION_ID,
            _state=STATE,
            serve_nodes=self.SERVE_NODES,
            default_storage_type=STORAGE_TYPE_SSD,
        )
        self.assertEqual(cluster.cluster_id, self.CLUSTER_ID)
        self.assertIs(cluster._instance, instance)
        self.assertEqual(cluster.location_id, self.LOCATION_ID)
        self.assertEqual(cluster.state, STATE)
        self.assertEqual(cluster.serve_nodes, self.SERVE_NODES)
        self.assertEqual(cluster.default_storage_type, STORAGE_TYPE_SSD)

    def test_name_property(self):
        credentials = _make_credentials()
        client = self._make_client(
            project=self.PROJECT, credentials=credentials, admin=True
        )
        instance = _Instance(self.INSTANCE_ID, client)
        cluster = self._make_one(self.CLUSTER_ID, instance)

        self.assertEqual(cluster.name, self.CLUSTER_NAME)

    def test_from_pb_success(self):
        from google.cloud.bigtable_admin_v2.proto import instance_pb2 as data_v2_pb2
        from google.cloud.bigtable import enums

        client = _Client(self.PROJECT)
        instance = _Instance(self.INSTANCE_ID, client)

        location = self.LOCATION_PATH + self.LOCATION_ID
        state = enums.Cluster.State.RESIZING
        storage_type = enums.StorageType.SSD
        cluster_pb = data_v2_pb2.Cluster(
            name=self.CLUSTER_NAME,
            location=location,
            state=state,
            serve_nodes=self.SERVE_NODES,
            default_storage_type=storage_type,
        )

        klass = self._get_target_class()
        cluster = klass.from_pb(cluster_pb, instance)
        self.assertIsInstance(cluster, klass)
        self.assertEqual(cluster._instance, instance)
        self.assertEqual(cluster.cluster_id, self.CLUSTER_ID)
        self.assertEqual(cluster.location_id, self.LOCATION_ID)
        self.assertEqual(cluster.state, state)
        self.assertEqual(cluster.serve_nodes, self.SERVE_NODES)
        self.assertEqual(cluster.default_storage_type, storage_type)

    def test_from_pb_bad_cluster_name(self):
        from google.cloud.bigtable_admin_v2.proto import instance_pb2 as data_v2_pb2

        bad_cluster_name = "BAD_NAME"

        cluster_pb = data_v2_pb2.Cluster(name=bad_cluster_name)

        klass = self._get_target_class()
        with self.assertRaises(ValueError):
            klass.from_pb(cluster_pb, None)

    def test_from_pb_instance_id_mistmatch(self):
        from google.cloud.bigtable_admin_v2.proto import instance_pb2 as data_v2_pb2

        ALT_INSTANCE_ID = "ALT_INSTANCE_ID"
        client = _Client(self.PROJECT)
        instance = _Instance(ALT_INSTANCE_ID, client)

        self.assertNotEqual(self.INSTANCE_ID, ALT_INSTANCE_ID)
        cluster_pb = data_v2_pb2.Cluster(name=self.CLUSTER_NAME)

        klass = self._get_target_class()
        with self.assertRaises(ValueError):
            klass.from_pb(cluster_pb, instance)

    def test_from_pb_project_mistmatch(self):
        from google.cloud.bigtable_admin_v2.proto import instance_pb2 as data_v2_pb2

        ALT_PROJECT = "ALT_PROJECT"
        client = _Client(project=ALT_PROJECT)
        instance = _Instance(self.INSTANCE_ID, client)

        self.assertNotEqual(self.PROJECT, ALT_PROJECT)
        cluster_pb = data_v2_pb2.Cluster(name=self.CLUSTER_NAME)

        klass = self._get_target_class()
        with self.assertRaises(ValueError):
            klass.from_pb(cluster_pb, instance)

    def test___eq__(self):
        client = _Client(self.PROJECT)
        instance = _Instance(self.INSTANCE_ID, client)
        cluster1 = self._make_one(self.CLUSTER_ID, instance, self.LOCATION_ID)
        cluster2 = self._make_one(self.CLUSTER_ID, instance, self.LOCATION_ID)
        self.assertEqual(cluster1, cluster2)

    def test___eq__type_differ(self):
        client = _Client(self.PROJECT)
        instance = _Instance(self.INSTANCE_ID, client)
        cluster1 = self._make_one(self.CLUSTER_ID, instance, self.LOCATION_ID)
        cluster2 = object()
        self.assertNotEqual(cluster1, cluster2)

    def test___ne__same_value(self):
        client = _Client(self.PROJECT)
        instance = _Instance(self.INSTANCE_ID, client)
        cluster1 = self._make_one(self.CLUSTER_ID, instance, self.LOCATION_ID)
        cluster2 = self._make_one(self.CLUSTER_ID, instance, self.LOCATION_ID)
        comparison_val = cluster1 != cluster2
        self.assertFalse(comparison_val)

    def test___ne__(self):
        client = _Client(self.PROJECT)
        instance = _Instance(self.INSTANCE_ID, client)
        cluster1 = self._make_one("cluster_id1", instance, self.LOCATION_ID)
        cluster2 = self._make_one("cluster_id2", instance, self.LOCATION_ID)
        self.assertNotEqual(cluster1, cluster2)


class _Instance(object):
    def __init__(self, instance_id, client):
        self.instance_id = instance_id
        self._client = client

    def __eq__(self, other):
        return other.instance_id == self.instance_id and other._client == self._client


class _Client(object):
    def __init__(self, project):
        self.project = project
        self.project_name = "projects/" + self.project
        self._operations_stub = mock.sentinel.operations_stub

    def __eq__(self, other):
        return other.project == self.project and other.project_name == self.project_name