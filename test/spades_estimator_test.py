import unittest
import os
import time

from os import environ
from ConfigParser import ConfigParser
import psutil

import requests
from biokbase.workspace.client import Workspace as workspaceService  # @UnresolvedImport @IgnorePep8
from biokbase.workspace.client import ServerError as WorkspaceError  # @UnresolvedImport @IgnorePep8
from biokbase.AbstractHandle.Client import AbstractHandle as HandleService  # @UnresolvedImport @IgnorePep8
from kb_SPAdes.kb_SPAdesImpl import kb_SPAdes
from installed_clients.baseclient import ServerError
from installed_clients.ReadsUtilsClient import ReadsUtils
from kb_SPAdes.kb_SPAdesServer import MethodContext
from pprint import pprint
import shutil
import inspect
from kb_SPAdes.utils.estimator import estimate_metaSPAdes_reqs
import mock



class SimpleMockWs():
    """
    Mocks out a couple simple workspace commands.
    Intended only for local use against the spades estimator.
    Workspace / object ids are effectively random on each return.
    expects ObjectSpecification inputs to be "ref" with "ws_name/obj_name" formatting.
    """

    ws_mapping = dict()
    # Structured like this:
    # {
    #     ws_name : {
    #         id: int,
    #         objects: {
    #             name1: int,
    #             name2: int, ...etc
    #         }
    #     }
    # }

    def __init__(self, *args, **kwargs):
        self.ws_mapping = dict()
        self.skip_even_meta = kwargs.get("skip_even_meta", False)

    def get_object_info3(self, params):
        ret_val = {
            "infos": [],
            "paths": []
        }
        for o in params["objects"]:
            self._setup_ids(o)
            ret_val["infos"].append(self._object_info(o, with_meta=params.get("includeMetadata", 0)==1))
            ret_val["paths"].append(self._object_to_path(o))
        return ret_val

    def _setup_ids(self, obj):
        if "ref" in obj:
            split_ref = obj["ref"].split("/")
            ws_name, obj_name = split_ref[:2]
        if "workspace" in obj:
            ws_name = obj["workspace"]
        if "name" in obj:
            obj_name = obj["name"]
        if ws_name not in self.ws_mapping:
            ws_id = len(self.ws_mapping) + 1
            self.ws_mapping[ws_name] = {
                "id": ws_id,
                "objects": {}
            }
        if obj_name not in self.ws_mapping[ws_name]:
            self.ws_mapping[ws_name]["objects"][obj_name] = len(self.ws_mapping[ws_name]["objects"]) + 1

    def _object_to_path(self, obj):
        ws_name, obj_name = obj["ref"].split("/")[:2]
        return "/".join([
            str(self.ws_mapping[ws_name]['id']),
            str(self.ws_mapping[ws_name]['objects'][obj_name]),
            "1"
        ])

    def _object_info(self, obj, with_meta=False):
        ws_name, obj_name = obj["ref"].split("/")[:2]
        ws_id = self.ws_mapping[ws_name]["id"]
        obj_id = self.ws_mapping[ws_name]["objects"][obj_name]
        meta = {}
        if with_meta and not (obj_id % 2 == 0 and self.skip_even_meta):
            meta = {
                "read_count": "10000",
                "read_length_mean": "100.0",
                "total_bases": "1000000"
            }
        return [obj_id, obj_name, "KBaseFile.PairedEndLibrary-2.2", "some_timestamp", 1, "some_user", ws_id, ws_name, "some_hash", 123, meta]


class SpadesEstimatorTestCase(unittest.TestCase):
    simple_params = {
        "workspace_name": "SomeWs",
        "read_libraries": ["SomeWs/Lib1", "SomeWs/Lib2", "SomeWs/Lib3", "Lib4"]
    }

    @classmethod
    def setUpClass(cls):
        cls.token = environ.get('KB_AUTH_TOKEN')
        cls.callbackURL = environ.get('SDK_CALLBACK_URL')
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': cls.token,
                        'provenance': [
                            {'service': 'kb_SPAdes',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_SPAdes'):
            cls.cfg[nameval[0]] = nameval[1]
        cls.cfg["SDK_CALLBACK_URL"] = cls.callbackURL
        cls.cfg["KB_AUTH_TOKEN"] = cls.token
        cls.serviceImpl = kb_SPAdes(cls.cfg)

    def test_estimator(self):
        ws = SimpleMockWs()
        est = estimate_metaSPAdes_reqs(self.simple_params, ws)
        self.assertEqual(est["cpus"], 16)
        self.assertEqual(est["walltime"], 300)
        self.assertEqual(est["memory"], 18453)

    def test_estimator_bad_inputs(self):
        ws = SimpleMockWs()
        with self.assertRaises(ValueError) as e:
            estimate_metaSPAdes_reqs({ "read_libraries": ['some_lib'] }, ws)
        self.assertIn("workspace_name is required to estimate metaSPAdes requirements!", str(e.exception))

        with self.assertRaises(ValueError) as e:
            estimate_metaSPAdes_reqs({ "workspace_name": "foo" }, ws)
        self.assertIn("At least one read library is required to estimate metaSPAdes requirements!", str(e.exception))

        with self.assertRaises(ValueError) as e:
            estimate_metaSPAdes_reqs({ "workspace_name": "foo", "read_libraries": [] }, ws)
        self.assertIn("At least one read library is required to estimate metaSPAdes requirements!", str(e.exception))

    def test_estimator_missing_meta(self):
        ws = SimpleMockWs(skip_even_meta=True)
        est = estimate_metaSPAdes_reqs(self.simple_params, ws)
        self.assertEqual(est["cpus"], 16)
        self.assertEqual(est["walltime"], 300)
        self.assertEqual(est["memory"], 18453)

    @mock.patch('kb_SPAdes.kb_SPAdesImpl.Workspace', SimpleMockWs)
    def test_estimator_impl_simple(self):
        est = self.serviceImpl.estimate_metaSPAdes_requirements(self.ctx, self.simple_params)[0]
        self.assertEqual(est["cpus"], 16)
        self.assertEqual(est["walltime"], 300)
        self.assertEqual(est["memory"], 18453)
