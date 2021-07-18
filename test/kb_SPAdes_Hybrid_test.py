from __future__ import print_function
import unittest
import os
import time
import json

from os import environ
from configparser import ConfigParser
import psutil
from pprint import pprint
import shutil
import inspect
import requests

from installed_clients.AbstractHandleClient import AbstractHandle as HandleService
from kb_SPAdes.kb_SPAdesImpl import kb_SPAdes
from installed_clients.ReadsUtilsClient import ReadsUtils
from kb_SPAdes.kb_SPAdesServer import MethodContext
from installed_clients.WorkspaceClient import Workspace
from kb_SPAdes.utils.spades_assembler import SPAdesAssembler
from kb_SPAdes.utils.spades_utils import SPAdesUtils


class hybrid_SPAdesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.token = environ.get('KB_AUTH_TOKEN')
        cls.callbackURL = environ.get('SDK_CALLBACK_URL')
        print('CB URL: ' + cls.callbackURL)
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
        cls.wsURL = cls.cfg['workspace-url']
        cls.shockURL = cls.cfg['shock-url']
        cls.hs = HandleService(url=cls.cfg['handle-service-url'],
                               token=cls.token)
        # cls.wsClient = workspaceService(cls.wsURL, token=cls.token)
        cls.wsClient = Workspace(cls.wsURL, token=cls.token)
        wssuffix = int(time.time() * 1000)
        wsName = "test_kb_SPAdes_" + str(wssuffix)
        cls.wsinfo = cls.wsClient.create_workspace({'workspace': wsName})
        print('created workspace ' + cls.getWsName())

        cls.SPAdes_PROJECT_DIR = 'spades_outputs'
        cls.scratch = cls.cfg['scratch']
        if not os.path.exists(cls.scratch):
            os.makedirs(cls.scratch)
        cls.spades_prjdir = os.path.join(cls.scratch, cls.SPAdes_PROJECT_DIR)
        if not os.path.exists(cls.spades_prjdir):
            os.makedirs(cls.spades_prjdir)
        cls.spades_assembler = SPAdesAssembler(cls.cfg, cls.ctx.provenance)
        cls.spades_utils = SPAdesUtils(cls.spades_prjdir, cls.cfg)
        cls.serviceImpl = kb_SPAdes(cls.cfg)

        cls.readUtilsImpl = ReadsUtils(cls.callbackURL, token=cls.token)
        cls.staged = {}
        cls.nodes_to_delete = []
        cls.handles_to_delete = []
        cls.setupTestData()
        print('\n\n=============== Starting HybridSPAdes tests ==================')

    @classmethod
    def tearDownClass(cls):

        print('\n\n=============== Cleaning up ==================')

        if hasattr(cls, 'wsinfo'):
            cls.wsClient.delete_workspace({'workspace': cls.getWsName()})
            print('Test workspace was deleted: ' + cls.getWsName())
        if hasattr(cls, 'nodes_to_delete'):
            for node in cls.nodes_to_delete:
                cls.delete_shock_node(node)
        if hasattr(cls, 'handles_to_delete'):
            if cls.handles_to_delete:
                cls.hs.delete_handles(cls.hs.hids_to_handles(cls.handles_to_delete))
                print('Deleted handles ' + str(cls.handles_to_delete))

    @classmethod
    def getWsName(cls):
        return cls.wsinfo[1]

    def getImpl(self):
        return self.serviceImpl

    @classmethod
    def delete_shock_node(cls, node_id):
        header = {'Authorization': 'Oauth {0}'.format(cls.token)}
        requests.delete(cls.shockURL + '/node/' + node_id, headers=header,
                        allow_redirects=True)
        print('Deleted shock node ' + node_id)

    # Helper script borrowed from the transform service, logger removed
    @classmethod
    def upload_file_to_shock(cls, file_path):
        """
        Use HTTP multi-part POST to save a file to a SHOCK instance.
        """

        header = dict()
        header["Authorization"] = "Oauth {0}".format(cls.token)

        if file_path is None:
            raise Exception("No file given for upload to SHOCK!")

        with open(os.path.abspath(file_path), 'rb') as dataFile:
            files = {'upload': dataFile}
            print('POSTing data')
            response = requests.post(
                cls.shockURL + '/node', headers=header, files=files,
                stream=True, allow_redirects=True)
            print('got response')

        if not response.ok:
            response.raise_for_status()

        result = response.json()

        if result['error']:
            raise Exception(result['error'][0])
        else:
            return result["data"]

    @classmethod
    def upload_file_to_shock_and_get_handle(cls, test_file):
        '''
        Uploads the file in test_file to shock and returns the node and a
        handle to the node.
        '''
        print('loading file to shock: ' + test_file)
        node = cls.upload_file_to_shock(test_file)
        pprint(node)
        cls.nodes_to_delete.append(node['id'])

        print('creating handle for shock id ' + node['id'])
        handle_id = cls.hs.persist_handle({'id': node['id'],
                                           'type': 'shock',
                                           'url': cls.shockURL
                                           })
        cls.handles_to_delete.append(handle_id)

        md5 = node['file']['checksum']['md5']
        return node['id'], handle_id, md5, node['file']['size']

    @classmethod
    def upload_reads(cls, wsobjname, object_body, fwd_reads,
                     rev_reads=None, single_end=False, sequencing_tech='Illumina',
                     single_genome='1'):

        ob = dict(object_body)  # copy
        ob['sequencing_tech'] = sequencing_tech
        ob['wsname'] = cls.getWsName()
        ob['name'] = wsobjname
        if single_end or rev_reads:
            ob['interleaved'] = 0
        else:
            ob['interleaved'] = 1
        print('\n===============staging data for object ' + wsobjname +
              '================')
        print('uploading forward reads file ' + fwd_reads['file'])
        fwd_id, fwd_handle_id, fwd_md5, fwd_size = \
            cls.upload_file_to_shock_and_get_handle(fwd_reads['file'])

        ob['fwd_id'] = fwd_id
        rev_id = None
        rev_handle_id = None
        if rev_reads:
            print('uploading reverse reads file ' + rev_reads['file'])
            rev_id, rev_handle_id, rev_md5, rev_size = \
                cls.upload_file_to_shock_and_get_handle(rev_reads['file'])
            ob['rev_id'] = rev_id
        obj_ref = cls.readUtilsImpl.upload_reads(ob)
        objdata = cls.wsClient.get_object_info_new({
            'objects': [{'ref': obj_ref['obj_ref']}]
            })[0]
        cls.staged[wsobjname] = {'info': objdata,
                                 'ref': cls.make_ref(objdata),
                                 'fwd_node_id': fwd_id,
                                 'rev_node_id': rev_id,
                                 'fwd_handle_id': fwd_handle_id,
                                 'rev_handle_id': rev_handle_id
                                 }

    @classmethod
    def upload_assembly(cls, wsobjname, object_body, fwd_reads,
                        rev_reads=None, kbase_assy=False,
                        single_end=False, sequencing_tech='Illumina'):
        if single_end and rev_reads:
            raise ValueError('u r supr dum')

        print('\n===============staging data for object ' + wsobjname +
              '================')
        print('uploading forward reads file ' + fwd_reads['file'])
        fwd_id, fwd_handle_id, fwd_md5, fwd_size = \
            cls.upload_file_to_shock_and_get_handle(fwd_reads['file'])
        fwd_handle = {
                      'hid': fwd_handle_id,
                      'file_name': fwd_reads['name'],
                      'id': fwd_id,
                      'url': cls.shockURL,
                      'type': 'shock',
                      'remote_md5': fwd_md5
                      }

        ob = dict(object_body)  # copy
        ob['sequencing_tech'] = sequencing_tech
        if kbase_assy:
            if single_end:
                wstype = 'KBaseAssembly.SingleEndLibrary'
                ob['handle'] = fwd_handle
            else:
                wstype = 'KBaseAssembly.PairedEndLibrary'
                ob['handle_1'] = fwd_handle
        else:
            if single_end:
                wstype = 'KBaseFile.SingleEndLibrary'
                obkey = 'lib'
            else:
                wstype = 'KBaseFile.PairedEndLibrary'
                obkey = 'lib1'
            ob[obkey] = \
                {'file': fwd_handle,
                 'encoding': 'UTF8',
                 'type': fwd_reads['type'],
                 'size': fwd_size
                 }

        rev_id = None
        rev_handle_id = None
        if rev_reads:
            print('uploading reverse reads file ' + rev_reads['file'])
            rev_id, rev_handle_id, rev_md5, rev_size = \
                cls.upload_file_to_shock_and_get_handle(rev_reads['file'])
            rev_handle = {
                          'hid': rev_handle_id,
                          'file_name': rev_reads['name'],
                          'id': rev_id,
                          'url': cls.shockURL,
                          'type': 'shock',
                          'remote_md5': rev_md5
                          }
            if kbase_assy:
                ob['handle_2'] = rev_handle
            else:
                ob['lib2'] = \
                    {'file': rev_handle,
                     'encoding': 'UTF8',
                     'type': rev_reads['type'],
                     'size': rev_size
                     }

        print('Saving object data')
        objdata = cls.wsClient.save_objects({
            'workspace': cls.getWsName(),
            'objects': [
                        {
                         'type': wstype,
                         'data': ob,
                         'name': wsobjname
                         }]
            })[0]
        print('Saved object objdata: ')
        pprint(objdata)
        print('Saved object ob: ')
        pprint(ob)
        cls.staged[wsobjname] = {'info': objdata,
                                 'ref': cls.make_ref(objdata),
                                 'fwd_node_id': fwd_id,
                                 'rev_node_id': rev_id,
                                 'fwd_handle_id': fwd_handle_id,
                                 'rev_handle_id': rev_handle_id
                                 }

    @classmethod
    def upload_empty_data(cls, wsobjname):
        objdata = cls.wsClient.save_objects({
            'workspace': cls.getWsName(),
            'objects': [{'type': 'Empty.AType',
                         'data': {},
                         'name': 'empty'
                         }]
            })[0]
        cls.staged[wsobjname] = {'info': objdata,
                                 'ref': cls.make_ref(objdata),
                                 }

    @classmethod
    def setupTestData(cls):
        print('Shock url ' + cls.shockURL)
        # print('WS url ' + cls.wsClient.url)
        # print('Handle service url ' + cls.hs.url)
        print('CPUs detected ' + str(psutil.cpu_count()))
        print('Available memory ' + str(psutil.virtual_memory().available))
        print('staging data')

        # get file type from type
        fwd_reads = {'file': 'data/small.forward.fq',
                     'name': 'test_fwd.fastq',
                     'type': 'fastq'}
        # get file type from handle file name
        rev_reads = {'file': 'data/small.reverse.fq',
                     'name': 'test_rev.FQ',
                     'type': ''}
        # get file type from shock node file name
        int_reads = {'file': 'data/interleaved.fq',
                     'name': '',
                     'type': ''}
        int64_reads = {'file': 'data/interleaved64.fq',
                       'name': '',
                       'type': ''}
        pacbio_reads = {'file': 'data/pacbio_filtered_small.fastq.gz',
                        'name': '',
                        'type': ''}
        pacbio_ccs_reads = {'file': 'data/pacbioCCS_small.fastq.gz',
                            'name': '',
                            'type': ''}
        iontorrent_reads = {'file': 'data/IonTorrent_single.fastq.gz',
                            'name': '',
                            'type': ''}
        plasmid1_reads = {'file': 'data/pl1.fq.gz',
                          'name': '',
                          'type': ''}
        plasmid2_reads = {'file': 'data/pl2.fq.gz',
                          'name': '',
                          'type': ''}
        cls.upload_reads('frbasic', {}, fwd_reads, rev_reads=rev_reads)
        cls.upload_reads('intbasic', {'single_genome': 1}, int_reads)
        cls.upload_reads('intbasic64', {'single_genome': 1}, int64_reads)
        cls.upload_reads('pacbio', {'single_genome': 1}, pacbio_reads,
                         single_end=True, sequencing_tech="PacBio CLR")
        cls.upload_reads('pacbioccs', {'single_genome': 1}, pacbio_ccs_reads,
                         single_end=True, sequencing_tech="PacBio CCS")
        cls.upload_reads('iontorrent', {'single_genome': 1}, iontorrent_reads,
                         single_end=True, sequencing_tech="IonTorrent")
        cls.upload_reads('meta', {'single_genome': 0}, fwd_reads, rev_reads=rev_reads)
        cls.upload_reads('meta2', {'single_genome': 0}, fwd_reads, rev_reads=rev_reads)
        cls.upload_reads('meta_single_end', {'single_genome': 0}, fwd_reads, single_end=True)
        cls.upload_reads('reads_out', {'read_orientation_outward': 1}, int_reads)
        cls.upload_assembly('frbasic_kbassy', {}, fwd_reads, rev_reads=rev_reads, kbase_assy=True)
        cls.upload_assembly('intbasic_kbassy', {}, int_reads, kbase_assy=True)
        cls.upload_reads('single_end', {}, fwd_reads, single_end=True)
        cls.upload_reads('single_end2', {}, rev_reads, single_end=True)
        cls.upload_reads('plasmid_reads', {'single_genome': 1},
                         plasmid1_reads, rev_reads=plasmid2_reads)
        shutil.copy2('data/small.forward.fq', 'data/small.forward.bad')
        bad_fn_reads = {'file': 'data/small.forward.bad',
                        'name': '',
                        'type': ''}
        cls.upload_assembly('bad_shk_name', {}, bad_fn_reads)
        bad_fn_reads['file'] = 'data/small.forward.fq'
        bad_fn_reads['name'] = 'file.terrible'
        cls.upload_assembly('bad_file_name', {}, bad_fn_reads)
        bad_fn_reads['name'] = 'small.forward.fastq'
        bad_fn_reads['type'] = 'xls'
        cls.upload_assembly('bad_file_type', {}, bad_fn_reads)
        cls.upload_assembly('bad_node', {}, fwd_reads)
        cls.delete_shock_node(cls.nodes_to_delete.pop())
        cls.upload_empty_data('empty')
        print('Data staged.')

    @classmethod
    def make_ref(self, object_info):
        return str(object_info[6]) + '/' + str(object_info[0]) + \
            '/' + str(object_info[4])

    def run_hybrid_success(self, readnames, output_name, longreadnames=None,
                           min_contig_length=0, dna_source=None, kmer_sizes=None,
                           orientation='fr', lib_type='paired-end',
                           long_reads_type='pacbio_clr'):
        """
        run_hybrid_success: The main method to test all possible hybrid input data sets
        """
        test_name = inspect.stack()[1][3]
        print('\n**** starting expected success test: ' + test_name + ' *****')
        print('   libs: ' + str(readnames))

        print("READNAMES: " + str(readnames))
        print("STAGED: " + str(self.staged))

        libs = [{'lib_ref': self.staged[n]['ref'],
                 'orientation': orientation,
                 'lib_type': lib_type} for n in readnames]

        params = {'workspace_name': self.getWsName(),
                  'reads_libraries': libs,
                  'output_contigset_name': output_name,
                  'min_contig_length': min_contig_length,
                  'create_report': 1
                  }

        if longreadnames:
            long_libs = [{'long_reads_ref': self.staged[n]['ref'],
                          'long_reads_type': long_reads_type} for n in longreadnames]
            params['long_reads_libraries'] = long_libs

        if not (dna_source is None):
            if dna_source == 'None':
                params['dna_source'] = None
            else:
                params['dna_source'] = dna_source

        ret = self.getImpl().run_HybridSPAdes(self.ctx, params)[0]
        if params.get('create_report', 0) == 1:
            self.assertReportAssembly(ret, output_name)

    def assertReportAssembly(self, ret_obj, assembly_name):
        """
        assertReportAssembly: given a report object, check the object existence
        """
        report = self.wsClient.get_objects2({
                        'objects': [{'ref': ret_obj['report_ref']}]})['data'][0]
        self.assertEqual('KBaseReport.Report', report['info'][2].split('-')[0])
        self.assertEqual(1, len(report['data']['objects_created']))
        self.assertEqual('Assembled contigs',
                         report['data']['objects_created'][0]['description'])
        self.assertIn('Assembled into ', report['data']['text_message'])
        self.assertIn('contigs', report['data']['text_message'])
        print("**************Report Message*************\n")
        print(report['data']['text_message'])

        assembly_ref = report['data']['objects_created'][0]['ref']
        assembly = self.wsClient.get_objects([{'ref': assembly_ref}])[0]

        self.assertEqual('KBaseGenomeAnnotations.Assembly', assembly['info'][2].split('-')[0])
        self.assertEqual(1, len(assembly['provenance']))
        self.assertEqual(assembly_name, assembly['data']['assembly_id'])

        temp_handle_info = self.hs.hids_to_handles([assembly['data']['fasta_handle_ref']])
        assembly_fasta_node = temp_handle_info[0]['id']
        self.nodes_to_delete.append(assembly_fasta_node)

    # Uncomment to skip this test
    # @unittest.skip("skipped test_fr_pair_kbfile")
    def test_fr_pair_kbfile(self):
        self.run_hybrid_success(
            ['frbasic'], 'frbasic_out')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_fr_pair_kbassy")
    def test_fr_pair_kbassy(self):
        self.run_hybrid_success(
            ['frbasic_kbassy'], 'frbasic_kbassy_out')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_interlaced_kbfile")
    def test_interlaced_kbfile(self):
        self.run_hybrid_success(
            ['intbasic'], 'intbasic_out')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_interlaced_kbassy")
    def test_interlaced_kbassy(self):
        self.run_hybrid_success(
            ['intbasic_kbassy'], 'intbasic_kbassy_out',
            dna_source='')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_multiple")
    def test_multiple(self):
        self.run_hybrid_success(
            ['intbasic_kbassy', 'frbasic'], 'multiple_out',
            dna_source='None')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_plasmid_kbfile")
    def test_plasmid_kbfile(self):
        self.run_hybrid_success(
            ['plasmid_reads'], 'plasmid_out',
            dna_source='plasmid')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_multiple_single")
    def test_multiple_single(self):
        self.run_hybrid_success(
            ['single_end', 'single_end2'], 'multiple_single_out',
            dna_source='None', lib_type='single')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_metagenome_kbfile")
    def test_metagenome_kbfile(self):
        self.run_hybrid_success(
            ['meta'], 'metabasic_out',
            dna_source='metagenomic')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_multiple_pacbio_single")
    def test_multiple_pacbio_single(self):
        self.run_hybrid_success(
            ['single_end'], 'pacbio_single_out', longreadnames=['pacbio'],
            lib_type='single', long_reads_type='pacbio_clr', dna_source='None')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_multiple_pacbio_illumina")
    def test_multiple_pacbio_illumina(self):
        self.run_hybrid_success(
            ['intbasic_kbassy'], 'pacbio_multiple_out', longreadnames=['pacbio'],
            lib_type='single', long_reads_type='pacbio_clr', dna_source='None')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_pacbioccs_alone")
    def test_pacbioccs_alone(self):
        self.run_hybrid_success(
            ['pacbioccs'], 'pacbioccs_alone_out', lib_type='single',
            dna_source='None')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_pacbioccs_single")
    def test_pacbioccs_single(self):
        self.run_hybrid_success(
            ['single_end'], 'pacbioccs_single_out', longreadnames=['pacbioccs'],
            lib_type='single', long_reads_type='pacbio_ccs', dna_source='None')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_multiple_pacbioccs_illumina")
    def test_multiple_pacbioccs_illumina(self):
        self.run_hybrid_success(
            ['intbasic_kbassy'], 'pacbioccs_multiple_out', longreadnames=['pacbioccs'],
            lib_type='single', long_reads_type='pacbio_ccs', dna_source='None')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_single_reads")
    def test_single_reads(self):
        self.run_hybrid_success(
            ['single_end'], 'single_out',
            lib_type='single', dna_source='None')

    # ########################End of passed tests######################

    # Uncomment to skip this test
    # @unittest.skip("skipped test_spades_utils_check_spades_params")
    def test_spades_utils_check_spades_params(self):
        """
        test_spades_utils_check_spades_params: check if parameters are given and set correctly
        """
        dna_src_list = ['single_cell',  # --sc
                        'metagenomic',  # --meta
                        'plasmid',  # --plasmid
                        'rna',  # --rna
                        'iontorrent'  # --iontorrent
                        ]

        pipeline_opts = None

        # test single_cell reads
        dnasrc = dna_src_list[0]
        rds_name = 'single_end'
        output_name = rds_name + '_out'
        libs1 = {'lib_ref':  self.staged[rds_name]['ref'],
                 'orientation': '',
                 'lib_type': 'single'}

        params = {'workspace_name': self.getWsName(),
                  'reads_libraries': [libs1],
                  'dna_source': dnasrc,
                  'output_contigset_name': output_name,
                  'pipeline_options': pipeline_opts,
                  'create_report': 0
                  }

        params0 = {'output_contigset_name': output_name,
                   'reads_libraries': [libs1]}
        err_msg = 'Parameter workspace_name is mandatory!'
        with self.assertRaises(ValueError) as context_manager:
            self.spades_utils.check_spades_params(params0)
            self.assertEqual(err_msg, str(context_manager.exception.message))

        params1 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs1]}
        err_msg = 'Parameter output_contigset_name is mandatory!'
        with self.assertRaises(ValueError) as context_manager:
            self.spades_utils.check_spades_params(params1)
            self.assertEqual(err_msg, str(context_manager.exception.message))

        params2 = {'workspace_name': self.getWsName(),
                   'output_contigset_name': output_name,
                   'reads_libraries': libs1}
        err_msg = 'Input reads must be a list.'
        with self.assertRaises(ValueError) as context_manager:
            self.spades_utils.check_spades_params(params2)
            self.assertEqual(err_msg, str(context_manager.exception.message))

        params3 = {'workspace_name': self.getWsName(),
                   'output_contigset_name': output_name}
        err_msg = 'At least one of parameters single_reads, pairedEnd_reads ' +\
                  'and mate_pair_reads is required.'
        with self.assertRaises(ValueError) as context_manager:
            self.spades_utils.check_spades_params(params3)
            self.assertEqual(err_msg, str(context_manager.exception.message))

        print('=============== raw parameters ==================')
        pprint(params)
        params = self.spades_utils.check_spades_params(params)
        self.assertIn('basic_options', params)
        self.assertEqual(params['basic_options'], ['-o', 'assemble_results', '--sc'])
        self.assertIn('pipeline_options', params)
        self.assertEqual(params['pipeline_options'], ['careful'])
        self.assertEqual(params['dna_source'], 'single_cell')
        self.assertEqual(params['output_contigset_name'], 'single_end_out')

    # Uncomment to skip this test
    # @unittest.skip("skipped test_spades_utils_get_hybrid_reads_info")
    def test_spades_utils_get_hybrid_reads_info(self):
        """
        test_spades_utils_get_hybrid_reads_info: given the input parameters,
        fetch the reads info a tuple of five reads data
        """
        dna_src_list = ['single_cell',  # --sc
                        'metagenomic',  # --meta
                        'plasmid',  # --plasmid
                        'rna',  # --rna
                        'iontorrent'  # --iontorrent
                        ]
        pipeline_opts = None

        # test single_cell reads
        dnasrc = dna_src_list[0]
        rds_name = 'single_end'
        output_name = rds_name + '_out'
        libs1 = {'lib_ref':  self.staged[rds_name]['ref'],
                 'orientation': '',
                 'lib_type': 'single'}

        params1 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs1],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'pipeline_options': pipeline_opts,
                   'create_report': 0
                   }
        pprint(params1)
        (sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs) \
            = self.spades_utils.get_hybrid_reads_info(params1)
        self.assertFalse(sgl_rds == [])
        self.assertTrue(pe_rds == [])
        self.assertTrue(mp_rds == [])
        self.assertTrue(pb_ccs == [])
        self.assertTrue(pb_clr == [])
        self.assertTrue(np_rds == [])
        self.assertTrue(sgr_rds == [])
        self.assertTrue(tr_ctgs == [])
        self.assertTrue(ut_ctgs == [])
        self.assertEqual(sgl_rds[0]['lib_type'], 'single')
        self.assertEqual(sgl_rds[0]['reads_ref'], self.staged[rds_name]['ref'])
        self.assertEqual(sgl_rds[0]['type'], 'single')
        self.assertEqual(sgl_rds[0]['seq_tech'], u'Illumina')
        self.assertIn(rds_name, sgl_rds[0]['reads_name'])
        self.assertIn('single.fastq', sgl_rds[0]['fwd_file'])

        # test pairedEnd_cell reads
        dnasrc = dna_src_list[0]
        rds_name = 'frbasic'
        output_name = rds_name + '_out'
        libs2 = {'lib_ref': self.staged[rds_name]['ref'],
                 'orientation': 'fr',
                 'lib_type': 'paired-end'}

        params2 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs2],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'pipeline_options': pipeline_opts,
                   'create_report': 0
                   }

        (sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs) \
            = self.spades_utils.get_hybrid_reads_info(params2)
        self.assertTrue(sgl_rds == [])
        self.assertFalse(pe_rds == [])
        self.assertTrue(mp_rds == [])
        self.assertTrue(pb_ccs == [])
        self.assertTrue(pb_clr == [])
        self.assertTrue(np_rds == [])
        self.assertEqual(pe_rds[0]['lib_type'], 'paired-end')
        self.assertEqual(pe_rds[0]['reads_ref'], self.staged[rds_name]['ref'])
        self.assertEqual(pe_rds[0]['type'], 'paired')
        self.assertEqual(pe_rds[0]['seq_tech'], u'Illumina')
        self.assertEqual(pe_rds[0]['orientation'], 'fr')
        self.assertIn(rds_name, pe_rds[0]['reads_name'])
        self.assertIn('fwd.fastq', pe_rds[0]['fwd_file'])
        self.assertIn('rev.fastq', pe_rds[0]['rev_file'])

        # test pairedEnd_cell reads with pacbio clr reads
        dnasrc = dna_src_list[0]
        rds_name2 = 'pacbio'
        output_name = rds_name + '_' + rds_name2 + '_out'
        libs4 = {'long_reads_ref': self.staged[rds_name2]['ref'],
                 'long_reads_type': 'pacbio_clr'}
        params4 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs2],
                   'long_reads_libraries': [libs4],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'pipeline_options': pipeline_opts,
                   'create_report': 0
                   }
        pprint(params4)
        (sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs) \
            = self.spades_utils.get_hybrid_reads_info(params4)
        self.assertTrue(sgl_rds == [])
        self.assertTrue(mp_rds == [])
        self.assertTrue(pb_ccs == [])
        self.assertTrue(sgr_rds == [])
        self.assertFalse(pe_rds == [])
        self.assertTrue(tr_ctgs == [])
        self.assertTrue(ut_ctgs == [])
        self.assertFalse(pb_clr == [])
        self.assertTrue(np_rds == [])
        self.assertEqual(pe_rds[0]['lib_type'], 'paired-end')
        self.assertEqual(pe_rds[0]['reads_ref'], self.staged[rds_name]['ref'])
        self.assertEqual(pe_rds[0]['type'], 'paired')
        self.assertEqual(pe_rds[0]['seq_tech'], u'Illumina')
        self.assertEqual(pe_rds[0]['orientation'], 'fr')
        self.assertIn(rds_name, pe_rds[0]['reads_name'])
        self.assertIn('fwd.fastq', pe_rds[0]['fwd_file'])
        self.assertIn('rev.fastq', pe_rds[0]['rev_file'])
        self.assertEqual(pb_clr[0]['long_reads_type'], 'pacbio_clr')
        self.assertEqual(pb_clr[0]['reads_ref'], self.staged[rds_name2]['ref'])
        self.assertEqual(pb_clr[0]['type'], 'single')
        self.assertEqual(pb_clr[0]['seq_tech'], u'PacBio CLR')
        self.assertEqual(pe_rds[0]['orientation'], 'fr')
        self.assertIn(rds_name2, pb_clr[0]['reads_name'])
        self.assertIn('single.fastq', pb_clr[0]['fwd_file'])

    # Uncomment to skip this test
    # @unittest.skip("skipped test_spades_utils_construct_yaml_dataset_file")
    def test_spades_utils_construct_yaml_dataset_file(self):
        """
        test_spades_utils_construct_yaml_dataset_file: given different reads libs,
        check if a yaml file is created correctly
        """
        dna_src_list = ['single_cell',  # --sc
                        'metagenomic',  # --meta
                        'plasmid',  # --plasmid
                        'rna',  # --rna
                        'iontorrent'  # --iontorrent
                        ]

        pipeline_opts = None

        # test single_cell reads
        dnasrc = dna_src_list[0]
        rds_name = 'single_end'
        output_name = rds_name + '_out'
        libs1 = {'lib_ref':  self.staged[rds_name]['ref'],
                 'orientation': '',
                 'lib_type': 'single'}

        params1 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs1],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'pipeline_options': pipeline_opts,
                   'create_report': 0
                   }
        (sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs) \
            = self.spades_utils.get_hybrid_reads_info(params1)
        yaml_file = self.spades_utils.construct_yaml_dataset_file(
                sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs)

        print('Yaml data saved to {}'.format(yaml_file))
        yaml_data = []
        try:
            with open(yaml_file, 'r') as yaml_file_hd:
                yaml_data = json.load(yaml_file_hd)
        except IOError as ioerr:
            print('Loading of the {} file raised error:\n'.format(yaml_file))
            pprint(ioerr)
        else:
            self.assertIn('single reads', yaml_data[0])
            self.assertIn('type', yaml_data[0])
            print(json.dumps(yaml_data, indent=1))

        # test pairedEnd_cell reads
        dnasrc = dna_src_list[0]
        rds_name = 'frbasic'
        output_name = rds_name + '_out'
        libs2 = {'lib_ref': self.staged[rds_name]['ref'],
                 'orientation': 'fr',
                 'lib_type': 'paired-end'}

        params2 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs2],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'pipeline_options': pipeline_opts,
                   'create_report': 0
                   }

        (sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs) \
            = self.spades_utils.get_hybrid_reads_info(params2)
        yaml_file = self.spades_utils.construct_yaml_dataset_file(
                sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs)
        print('Yaml data saved to {}'.format(yaml_file))
        yaml_data = []
        try:
            with open(yaml_file, 'r') as yaml_file:
                yaml_data = json.load(yaml_file)
        except IOError as ioerr:
            print('Loading of the {} file raised error:\n'.format(yaml_file))
            pprint(ioerr)
        else:
            self.assertIn('left reads', yaml_data[0])
            self.assertIn('right reads', yaml_data[0])
            self.assertIn('rev.fastq', yaml_data[0]['left reads'][0])
            self.assertIn('fwd.fastq', yaml_data[0]['right reads'][0])
            self.assertEqual(yaml_data[0]['orientation'], 'fr')
            self.assertEqual(yaml_data[0]['type'], 'paired-end')
            print(json.dumps(yaml_data, indent=1))

        # test pairedEnd_cell reads with pacbio clr reads
        dnasrc = dna_src_list[0]
        rds_name2 = 'pacbio'
        output_name = rds_name + '_' + rds_name2 + '_out'
        libs4 = {'long_reads_ref': self.staged[rds_name2]['ref'],
                 'long_reads_type': 'pacbio_clr'}
        params4 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs2],
                   'long_reads_libraries': [libs4],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'pipeline_options': pipeline_opts,
                   'create_report': 0
                   }
        (sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs) \
            = self.spades_utils.get_hybrid_reads_info(params4)
        yaml_file = self.spades_utils.construct_yaml_dataset_file(
                sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs)
        print('Yaml data saved to {}'.format(yaml_file))
        yaml_data = []
        try:
            with open(yaml_file, 'r') as yaml_file:
                yaml_data = json.load(yaml_file)
        except IOError as ioerr:
            print('Loading of the {} file raised error:\n'.format(yaml_file))
            pprint(ioerr)
        else:
            self.assertIn('left reads', yaml_data[0])
            self.assertIn('right reads', yaml_data[0])
            self.assertIn('rev.fastq', yaml_data[0]['left reads'][0])
            self.assertIn('fwd.fastq', yaml_data[0]['right reads'][0])
            self.assertEqual(yaml_data[0]['orientation'], 'fr')
            self.assertEqual(yaml_data[0]['type'], 'paired-end')
            self.assertIn('single reads', yaml_data[1])
            self.assertNotIn('right reads', yaml_data[1])
            self.assertIn('single.fastq', yaml_data[1]['single reads'][0])
            self.assertEqual(yaml_data[1]['type'], 'pacbio')
            print(json.dumps(yaml_data, indent=1))

    # Uncomment to skip this test
    # @unittest.skip("skipped test_spades_utils_run_assemble")
    def test_spades_utils_run_assemble(self):
        """
        test_spades_utils_utils_run_assemble: given different yaml_file and params,
        run hybrid SPAdes against the params
        [
            {
                'orientation': 'rf',
                'type': 'mate-pairs',
                'right reads': ['/FULL_PATH_TO_DATASET/lib_mp1_right.fastq'],
                'left reads': ['/FULL_PATH_TO_DATASET/lib_mp1_left.fastq']
            },
            {
                'type': 'single',
                'single reads': ['/FULL_PATH_TO_DATASET/pacbio_ccs.fastq']
            },
            {
                'type': 'pacbio',
                'single reads': ['/FULL_PATH_TO_DATASET/pacbio_clr.fastq']
            }
        ]
        """
        # test data dirs from SPAdes installation
        spades_test_data_set_dir = '/opt/SPAdes-3.13.0-Linux/share/spades/'
        ecoli_test_data_subdir = 'test_dataset'

        ecoli1 = os.path.join(spades_test_data_set_dir,
                              ecoli_test_data_subdir, 'ecoli_1K_1.fq.gz')
        ecoli2 = os.path.join(spades_test_data_set_dir,
                              ecoli_test_data_subdir, 'ecoli_1K_2.fq.gz')
        """
        plasmid_test_data_subdir = 'test_dataset_plasmid'
        truspades_test_data_subdir = 'test_dataset_truspades'
        pl1 = os.path.join(spades_test_data_set_dir,
                           plasmid_test_data_subdir, 'pl1.fq.gz')
        pl2 = os.path.join(spades_test_data_set_dir,
                           plasmid_test_data_subdir, 'pl2.fq.gz')
        A_R1 = os.path.join(spades_test_data_set_dir,
                            truspades_test_data_subdir, 'A_R1.fastq.gz')
        A_R2 = os.path.join(spades_test_data_set_dir,
                            truspades_test_data_subdir, 'A_R2.fastq.gz')
        B_R1 = os.path.join(spades_test_data_set_dir,
                            truspades_test_data_subdir, 'B_R1.fastq.gz')
        B_R2 = os.path.join(spades_test_data_set_dir,
                            truspades_test_data_subdir, 'B_R2.fastq.gz')

        pyyaml2 = os.path.join(spades_test_data_set_dir, 'pyyaml2')
        pyyaml3 = os.path.join(spades_test_data_set_dir, 'pyyaml3')
        """
        dna_src_list = ['single_cell',  # --sc
                        'metagenomic',  # --meta
                        'plasmid',  # --plasmid
                        'rna',  # --rna
                        'iontorrent'  # --iontorrent
                        ]

        pipeline_opts = None
        km_sizes = '21, 33, 55'

        # test single_cell reads
        dnasrc = dna_src_list[0]
        rds_name = 'single_end'
        output_name = rds_name + '_out'
        libs1 = {'lib_ref':  self.staged[rds_name]['ref'],
                 'orientation': '',
                 'lib_type': 'single'}

        params1 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs1],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'pipeline_options': pipeline_opts,
                   'create_report': 0
                   }

        spades_prjdir = os.path.join(self.spades_prjdir, rds_name)
        spades_assemble_dir = os.path.join(spades_prjdir, 'assemble_results')
        spades_utils = SPAdesUtils(spades_prjdir, self.cfg)
        params1 = spades_utils.check_spades_params(params1)

        (sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs) \
            = self.spades_utils.get_hybrid_reads_info(params1)
        single_yaml_file = self.spades_utils.construct_yaml_dataset_file(
                sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs)

        run_exit_code = 1
        run_exit_code = spades_utils.run_assemble(single_yaml_file, km_sizes, 'single_cell',
                                                  params1['basic_options'],
                                                  params1['pipeline_options'])
        print('{} HybridSPAdes assembling returns code= {}'.format(rds_name, run_exit_code))
        self.assertEqual(run_exit_code, 0)
        self.assertEqual(spades_prjdir, '/kb/module/work/tmp/spades_outputs/single_end')
        self.assertTrue(os.path.isdir(os.path.join(spades_assemble_dir, 'K21')))
        self.assertTrue(os.path.isdir(os.path.join(spades_assemble_dir, 'K33')))
        self.assertTrue(os.path.isdir(os.path.join(spades_assemble_dir, 'K55')))
        self.assertTrue(os.path.isdir(os.path.join(spades_assemble_dir, 'corrected')))
        self.assertTrue(os.path.isdir(os.path.join(spades_assemble_dir, 'misc')))
        self.assertTrue(os.path.isdir(os.path.join(spades_assemble_dir, 'tmp')))
        self.assertTrue(os.path.isdir(os.path.join(spades_assemble_dir, 'mismatch_corrector')))
        self.assertTrue(os.path.isfile(os.path.join(spades_assemble_dir, 'spades.log')))
        self.assertTrue(os.path.isfile(os.path.join(spades_assemble_dir, 'assembly_graph.fastg')))
        self.assertTrue(os.path.isfile(os.path.join(spades_assemble_dir,
                        'assembly_graph_with_scaffolds.gfa')))
        self.assertTrue(os.path.isfile(os.path.join(spades_assemble_dir, 'before_rr.fasta')))
        self.assertTrue(os.path.isfile(os.path.join(spades_assemble_dir, 'contigs.fasta')))
        self.assertTrue(os.path.isfile(os.path.join(spades_assemble_dir, 'contigs.paths')))
        self.assertTrue(os.path.isfile(os.path.join(spades_assemble_dir, 'dataset.info')))
        self.assertTrue(os.path.isfile(os.path.join(self.spades_prjdir, 'input_data_set.yaml')))
        self.assertTrue(os.path.isfile(os.path.join(spades_assemble_dir, 'params.txt')))
        self.assertTrue(os.path.isfile(os.path.join(spades_assemble_dir, 'scaffolds.fasta')))
        self.assertTrue(os.path.isfile(os.path.join(spades_assemble_dir,
                        'corrected', 'corrected.yaml')))

        # testing with SPAdes test reads from installation
        yaml_file_path = os.path.join(self.spades_prjdir, 'test_data_set.yaml')
        ecoli_ymal_data = [
            {
                'orientation': 'fr',
                'type': 'paired-end',
                'right reads': [ecoli1],
                'left reads': [ecoli2]
            }]
        basic_opts = ['-o', self.spades_prjdir]
        ecoli_exit_code = 1
        try:
            with open(yaml_file_path, 'w') as yaml_file:
                json.dump(ecoli_ymal_data, yaml_file)
        except IOError as ioerr:
            print('Creation of the {} file raised error:\n'.format(yaml_file_path))
            pprint(ioerr)
        else:
            ecoli_exit_code = self.spades_utils.run_assemble(yaml_file_path, km_sizes,
                                                             'single_cell', basic_opts)
        spades_prjdir = self.spades_prjdir
        self.assertEqual(ecoli_exit_code, 0)
        self.assertEqual(spades_prjdir, '/kb/module/work/tmp/spades_outputs')
        self.assertTrue(os.path.isdir(os.path.join(spades_prjdir, 'K21')))
        self.assertTrue(os.path.isdir(os.path.join(spades_prjdir, 'K33')))
        self.assertTrue(os.path.isdir(os.path.join(spades_prjdir, 'K55')))
        self.assertTrue(os.path.isdir(os.path.join(spades_prjdir, 'corrected')))
        self.assertTrue(os.path.isdir(os.path.join(spades_prjdir, 'misc')))
        self.assertTrue(os.path.isdir(os.path.join(spades_prjdir, 'tmp')))
        self.assertTrue(os.path.isdir(os.path.join(spades_prjdir, 'mismatch_corrector')))
        self.assertTrue(os.path.isfile(os.path.join(spades_prjdir, 'spades.log')))
        self.assertTrue(os.path.isfile(os.path.join(spades_prjdir, 'assembly_graph.fastg')))
        self.assertTrue(os.path.isfile(os.path.join(spades_prjdir,
                        'assembly_graph_with_scaffolds.gfa')))
        self.assertTrue(os.path.isfile(os.path.join(spades_prjdir, 'before_rr.fasta')))
        self.assertTrue(os.path.isfile(os.path.join(spades_prjdir, 'contigs.fasta')))
        self.assertTrue(os.path.isfile(os.path.join(spades_prjdir, 'contigs.paths')))
        self.assertTrue(os.path.isfile(os.path.join(spades_prjdir, 'dataset.info')))
        self.assertTrue(os.path.isfile(os.path.join(spades_prjdir, 'test_data_set.yaml')))
        self.assertTrue(os.path.isfile(os.path.join(spades_prjdir, 'params.txt')))
        self.assertTrue(os.path.isfile(os.path.join(spades_prjdir, 'scaffolds.fasta')))
        self.assertTrue(os.path.isfile(os.path.join(spades_prjdir,
                        'corrected', 'corrected.yaml')))

    # Uncomment to skip this test
    # @unittest.skip("skipped test_spades_assembler_run_hybrid_spades")
    def test_spades_assembler_run_hybrid_spades(self):
        """
        test_spades_utils_run_HybridSPAdes: given different params,
        create a yaml file and then run hybrid SPAdes against the params
        """
        dna_src_list = ['single_cell',  # --sc
                        'metagenomic',  # --meta
                        'plasmid',  # --plasmid
                        'rna',  # --rna
                        'iontorrent'  # --iontorrent
                        ]

        pipeline_opts = None

        # test single_cell reads
        dnasrc = dna_src_list[0]
        rds_name = 'single_end'
        output_name = rds_name + '_out'
        libs1 = {'lib_ref':  self.staged[rds_name]['ref'],
                 'orientation': '',
                 'lib_type': 'single'}

        params1 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs1],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'pipeline_options': pipeline_opts,
                   'create_report': 1
                   }
        ret = self.spades_assembler.run_hybrid_spades(params1)
        if params1.get('create_report', 0) == 1:
            self.assertReportAssembly(ret, output_name)

        # test pairedEnd_cell reads
        dnasrc = dna_src_list[0]
        rds_name = 'frbasic'
        output_name = rds_name + '_out'
        libs2 = {'lib_ref': self.staged[rds_name]['ref'],
                 'orientation': 'fr',
                 'lib_type': 'paired-end'}

        params2 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs2],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'pipeline_options': pipeline_opts,
                   'create_report': 1
                   }

        ret = self.spades_assembler.run_hybrid_spades(params2)
        if params2.get('create_report', 0) == 1:
            self.assertReportAssembly(ret, output_name)

        # test pairedEnd_cell reads with pacbio clr reads
        dnasrc = dna_src_list[0]
        rds_name2 = 'pacbio'
        output_name = rds_name + '_' + rds_name2 + '_out'
        libs4 = {'long_reads_ref': self.staged[rds_name2]['ref'],
                 'long_reads_type': 'pacbio_clr'}

        params4 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs2],
                   'long_reads_libraries': [libs4],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'pipeline_options': pipeline_opts,
                   'create_report': 1
                   }
        ret = self.spades_assembler.run_hybrid_spades(params4)
        if params4.get('create_report', 0) == 1:
            self.assertReportAssembly(ret, output_name)

        # test pairedEnd_cell reads with pacbio clr reads and min_contig_length
        output_name = rds_name + '_' + rds_name2 + '_mcl_out'
        params5 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs2],
                   'long_reads_libraries': [libs4],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'min_contig_length': 500,
                   'pipeline_options': pipeline_opts,
                   'create_report': 1
                   }
        ret = self.spades_assembler.run_hybrid_spades(params5)
        if params5.get('create_report', 0) == 1:
            self.assertReportAssembly(ret, output_name)

        # test pairedEnd_cell reads with pacbio clr reads and 0 min_contig_length
        output_name = rds_name + '_' + rds_name2 + '_0mcl_out'
        params6 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs2],
                   'long_reads_libraries': [libs4],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'min_contig_length': 0,
                   'pipeline_options': pipeline_opts,
                   'create_report': 1
                   }
        ret = self.spades_assembler.run_hybrid_spades(params6)
        if params6.get('create_report', 0) == 1:
            self.assertReportAssembly(ret, output_name)

        # test metagenome_kbfile
        output_name = 'metabasic_out1'
        dnasrc = dna_src_list[1]
        libs5 = {'lib_ref': self.staged['meta']['ref'],
                 'orientation': 'fr',
                 'lib_type': 'paired-end'}
        params7 = {'workspace_name': self.getWsName(),
                   'reads_libraries': [libs5],
                   'dna_source': dnasrc,
                   'output_contigset_name': output_name,
                   'min_contig_length': 0,
                   'pipeline_options': pipeline_opts,
                   'create_report': 1
                   }
        ret = self.spades_assembler.run_hybrid_spades(params7)
        if params6.get('create_report', 0) == 1:
            self.assertReportAssembly(ret, output_name)
