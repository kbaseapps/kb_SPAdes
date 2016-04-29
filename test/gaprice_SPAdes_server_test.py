from __future__ import print_function
import unittest
import os
import time

from os import environ
from ConfigParser import ConfigParser
import psutil

import requests
from biokbase.workspace.client import Workspace as workspaceService  # @UnresolvedImport @IgnorePep8
from biokbase.AbstractHandle.Client import AbstractHandle as HandleService  # @UnresolvedImport @IgnorePep8
from gaprice_SPAdes_test.gaprice_SPAdes_testImpl import gaprice_SPAdes_test, ShockException
from biokbase.workspace.client import ServerError as WorkspaceError  # @UnresolvedImport @IgnorePep8
from pprint import pprint
import shutil
import inspect


class gaprice_SPAdesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.token = environ.get('KB_AUTH_TOKEN', None)
        cls.ctx = {'token': cls.token,
                   'provenance': [
                        {'service': 'gaprice_SPAdes_test',
                         'method': 'please_never_use_it_in_production',
                         'method_params': []
                         }],
                   'authenticated': 1}
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('gaprice_SPAdes_test'):
            cls.cfg[nameval[0]] = nameval[1]
        cls.wsURL = cls.cfg['workspace-url']
        cls.shockURL = cls.cfg['shock-url']
        cls.hs = HandleService(url=cls.cfg['handle-service-url'],
                               token=cls.token)
        cls.wsClient = workspaceService(cls.wsURL, token=cls.token)
        wssuffix = int(time.time() * 1000)
        wsName = "test_gaprice_SPAdes_test_" + str(wssuffix)
        cls.wsinfo = cls.wsClient.create_workspace({'workspace': wsName})
        print('created workspace ' + cls.getWsName())
        cls.serviceImpl = gaprice_SPAdes_test(cls.cfg)
        cls.staged = {}
        cls.nodes_to_delete = []
        cls.handles_to_delete = []
        cls.setupTestData()
        print('\n\n=============== Starting tests ==================')

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
            cls.hs.delete_handles(cls.hs.ids_to_handles(cls.handles_to_delete))
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
    def upload_assembly(cls, wsobjname, object_body, fwd_reads,
                        rev_reads=None, kbase_assy=False, single_end=False):
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
        ob['sequencing_tech'] = 'fake data'
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
        print('Saved object: ')
        pprint(objdata)
        pprint(ob)
        cls.staged[wsobjname] = {'info': objdata,
                                 'ref': cls.make_ref(objdata),
                                 'fwd_node_id': fwd_id,
                                 'rev_node_id': rev_id
                                 }

    @classmethod
    def upload_empty_data(cls):
        cls.wsClient.save_objects({
            'workspace': cls.getWsName(),
            'objects': [{'type': 'Empty.AType',
                         'data': {},
                         'name': 'empty'
                         }]
            })

    @classmethod
    def setupTestData(cls):
        print('Shock url ' + cls.shockURL)
        print('WS url ' + cls.wsClient.url)
        print('Handle service url ' + cls.hs.url)
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
        cls.upload_assembly('frbasic', {}, fwd_reads, rev_reads=rev_reads)
        cls.upload_assembly('intbasic', {'single_genome': 1}, int_reads)
        cls.upload_assembly('meta', {'single_genome': 0}, int_reads)
        cls.upload_assembly('reads_out', {'read_orientation_outward': 1},
                            int_reads)
        cls.upload_assembly('frbasic_kbassy', {}, fwd_reads,
                            rev_reads=rev_reads, kbase_assy=True)
        cls.upload_assembly('intbasic_kbassy', {}, int_reads, kbase_assy=True)
        cls.upload_assembly('single_end', {}, fwd_reads, single_end=True)
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
        cls.upload_empty_data()
        print('Data staged.')

    @classmethod
    def make_ref(self, object_info):
        return str(object_info[6]) + '/' + str(object_info[0]) + \
            '/' + str(object_info[4])

    def test_fr_pair_kbfile(self):

        self.run_success(
            ['frbasic'], 'frbasic_out',
            {'contigs':
             [{'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_1_length_64822_cov_8.54567_ID_21',
               'length': 64822,
               'id': 'NODE_1_length_64822_cov_8.54567_ID_21',
               'md5': '8a67351c7d6416039c6f613c31b10764'
               },
              {'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_2_length_62607_cov_8.06011_ID_7',
               'length': 62607,
               'id': 'NODE_2_length_62607_cov_8.06011_ID_7',
               'md5': 'e99fade8814bdb861532f493e5deddbd'
               }],
             'md5': '09a27dd5107ad23ee2b7695aee8c09d0',
             'fasta_md5': '7f6093a7e56a8dc5cbf1343b166eda67'
             })

    def test_fr_pair_kbassy(self):

        self.run_success(
            ['frbasic_kbassy'], 'frbasic_kbassy_out',
            {'contigs':
             [{'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_1_length_64822_cov_8.54567_ID_21',
               'length': 64822,
               'id': 'NODE_1_length_64822_cov_8.54567_ID_21',
               'md5': '8a67351c7d6416039c6f613c31b10764'
               },
              {'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_2_length_62607_cov_8.06011_ID_7',
               'length': 62607,
               'id': 'NODE_2_length_62607_cov_8.06011_ID_7',
               'md5': 'e99fade8814bdb861532f493e5deddbd'
               }],
             'md5': '09a27dd5107ad23ee2b7695aee8c09d0',
             'fasta_md5': '7f6093a7e56a8dc5cbf1343b166eda67'
             })

    def test_interlaced_kbfile(self):

        self.run_success(
            ['intbasic'], 'intbasic_out',
            {'contigs':
             [{'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_1000_length_274_cov_1.11168_ID_9587',
               'length': 274,
               'id': 'NODE_1000_length_274_cov_1.11168_ID_9587',
               'md5': '1b00037a0f39ff0fcb577c4e7ff72cf1'
               },
              {'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_1001_length_274_cov_1.1066_ID_9589',
               'length': 274,
               'id': 'NODE_1001_length_274_cov_1.1066_ID_9589',
               'md5': 'c1c853543b2bba9211e574238b842869'
               }],
             'md5': 'affbb138ad3887c7d12e8ec28a9a8d52',
             'fasta_md5': 'b3012dec12e4b6042affc9a933b60f7a'
             }, contig_count=1449)

    def test_interlaced_kbassy(self):

        self.run_success(
            ['intbasic_kbassy'], 'intbasic_kbassy_out',
            {'contigs':
             [{'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_1000_length_274_cov_1.11168_ID_9587',
               'length': 274,
               'id': 'NODE_1000_length_274_cov_1.11168_ID_9587',
               'md5': '1b00037a0f39ff0fcb577c4e7ff72cf1'
               },
              {'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_1001_length_274_cov_1.1066_ID_9589',
               'length': 274,
               'id': 'NODE_1001_length_274_cov_1.1066_ID_9589',
               'md5': 'c1c853543b2bba9211e574238b842869'
               }],
             'md5': 'affbb138ad3887c7d12e8ec28a9a8d52',
             'fasta_md5': 'b3012dec12e4b6042affc9a933b60f7a'
             }, contig_count=1449, dna_source='')

    def test_multiple(self):
        self.run_success(
            ['intbasic_kbassy', 'frbasic'], 'multiple_out',
            {'contigs':
             [{'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_1_length_64822_cov_8.54567_ID_29',
               'length': 64822,
               'id': 'NODE_1_length_64822_cov_8.54567_ID_29',
               'md5': '8a67351c7d6416039c6f613c31b10764'
               },
              {'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_2_length_62607_cov_8.06011_ID_15',
               'length': 62607,
               'id': 'NODE_2_length_62607_cov_8.06011_ID_15',
               'md5': 'e99fade8814bdb861532f493e5deddbd'
               }],
             'md5': 'a1bfe0a6d53afb2f0a8c186d4265703a',
             'fasta_md5': '5b7d11cf6a1b01cb2857883a5dc74357'
             }, contig_count=6, dna_source='None')

    def test_single_cell(self):

        self.run_success(
            ['frbasic'], 'single_cell_out',
            {'contigs':
             [{'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_1_length_64822_cov_8.54567_ID_21',
               'length': 64822,
               'id': 'NODE_1_length_64822_cov_8.54567_ID_21',
               'md5': '8a67351c7d6416039c6f613c31b10764'
               },
              {'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_2_length_62607_cov_8.06011_ID_7',
               'length': 62607,
               'id': 'NODE_2_length_62607_cov_8.06011_ID_7',
               'md5': 'e99fade8814bdb861532f493e5deddbd'
               }],
             'md5': '09a27dd5107ad23ee2b7695aee8c09d0',
             'fasta_md5': '7f6093a7e56a8dc5cbf1343b166eda67'
             }, dna_source='single_cell')

    def test_metagenome(self):

        self.run_success(
            ['frbasic'], 'metagenome_out',
            {'contigs':
             [{'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_1_length_64819_cov_8.54977_ID_184',
               'length': 64819,
               'id': 'NODE_1_length_64819_cov_8.54977_ID_184',
               'md5': '319f720b2de1af6dc7f32a98c1d3048e'
               },
              {'description': 'Note MD5 is generated from uppercasing ' +
                              'the sequence',
               'name': 'NODE_2_length_62607_cov_8.06601_ID_257',
               'length': 62607,
               'id': 'NODE_2_length_62607_cov_8.06601_ID_257',
               'md5': '878ed3dfad7ccecd5bdfc8f5c2db00c4'
               }],
             'md5': '5951328d2b25b8d9f6248a9b0aa3c49a',
             'fasta_md5': 'fe801b181101b2be1e64885e167cdfcb'
             }, dna_source='metagenome')

    def test_no_workspace_param(self):

        self.run_error(
            ['foo'], 'workspace_name parameter is required', wsname=None)

    def test_no_workspace_name(self):

        self.run_error(
            ['foo'], 'workspace_name parameter is required', wsname='None')

    def test_bad_workspace_name(self):

        self.run_error(['foo'], 'Invalid workspace name bad|name',
                       wsname='bad|name')

    def test_non_extant_workspace(self):

        self.run_error(
            ['foo'], 'Object foo cannot be accessed: No workspace with name ' +
            'Ireallyhopethisworkspacedoesntexistorthistestwillfail exists',
            wsname='Ireallyhopethisworkspacedoesntexistorthistestwillfail',
            exception=WorkspaceError)

    def test_bad_lib_name(self):

        self.run_error(['bad&name'], 'Invalid workspace object name bad&name')

    def test_no_libs_param(self):

        self.run_error(None, 'read_libraries parameter is required')

    def test_no_libs_list(self):

        self.run_error('foo', 'read_libraries must be a list')

    def test_non_extant_lib(self):

        self.run_error(
            ['foo'], 'No object with name foo exists in workspace ' +
            str(self.wsinfo[0]), exception=WorkspaceError)

    def test_no_libs(self):

        self.run_error([], 'At least one reads library must be provided')

    def test_no_output_param(self):

        self.run_error(
            ['foo'], 'output_contigset_name parameter is required',
            output_name=None)

    def test_no_output_name(self):

        self.run_error(
            ['foo'], 'output_contigset_name parameter is required',
            output_name='')

    def test_bad_output_name(self):

        self.run_error(
            ['frbasic'], 'Invalid workspace object name bad*name',
            output_name='bad*name')

    def test_inconsistent_metagenomics_1(self):

        self.run_error(
            ['intbasic'],
            'Reads object intbasic (' + self.staged['intbasic']['ref'] +
            ') is marked as containing dna from a single genome but the ' +
            'assembly method was specified as metagenomic',
            dna_source='metagenome')

    def test_inconsistent_metagenomics_2(self):

        self.run_error(
            ['meta'],
            'Reads object meta (' + self.staged['meta']['ref'] +
            ') is marked as containing metagenomic data but the assembly ' +
            'method was not specified as metagenomic')

    def test_outward_reads(self):

        self.run_error(
            ['reads_out'],
            'Reads object reads_out (' + self.staged['reads_out']['ref'] +
            ') is marked as having outward oriented reads, which SPAdes ' +
            'does not support.')

    def test_bad_module(self):

        self.run_error(['empty'],
                       'Only the types KBaseAssembly.PairedEndLibrary and ' +
                       'KBaseFile.PairedEndLibrary are supported')

    def test_bad_type(self):

        self.run_error(['single_end'],
                       'Only the types KBaseAssembly.PairedEndLibrary and ' +
                       'KBaseFile.PairedEndLibrary are supported')

    def test_bad_shock_filename(self):

        self.run_error(
            ['bad_shk_name'],
            ('Reads object {} (bad_shk_name) contains a reads file stored ' +
             'in Shock node {} for which a valid filename could not be ' +
             'determined. In order of precedence:\n' +
             'File type is: \nHandle file name is: \n' +
             'Shock file name is: small.forward.bad\n' +
             'Acceptable extensions: .fq .fastq .fq.gz ' +
             '.fastq.gz').format(self.staged['bad_shk_name']['ref'],
                                 self.staged['bad_shk_name']['fwd_node_id']))

    def test_bad_handle_filename(self):

        self.run_error(
            ['bad_file_name'],
            ('Reads object {} (bad_file_name) contains a reads file stored ' +
             'in Shock node {} for which a valid filename could not be ' +
             'determined. In order of precedence:\n' +
             'File type is: \nHandle file name is: file.terrible\n' +
             'Shock file name is: small.forward.fq\n' +
             'Acceptable extensions: .fq .fastq .fq.gz ' +
             '.fastq.gz').format(self.staged['bad_file_name']['ref'],
                                 self.staged['bad_file_name']['fwd_node_id']))

    def test_bad_file_type(self):

        self.run_error(
            ['bad_file_type'],
            ('Reads object {} (bad_file_type) contains a reads file stored ' +
             'in Shock node {} for which a valid filename could not be ' +
             'determined. In order of precedence:\n' +
             'File type is: .xls\nHandle file name is: small.forward.fastq\n' +
             'Shock file name is: small.forward.fq\n' +
             'Acceptable extensions: .fq .fastq .fq.gz ' +
             '.fastq.gz').format(self.staged['bad_file_type']['ref'],
                                 self.staged['bad_file_type']['fwd_node_id']))

    def test_bad_shock_node(self):

        self.run_error(['bad_node'],
                       ('Error downloading reads for object {} (bad_node) ' +
                        'from shock node {}: Node not found').format(
                            self.staged['bad_node']['ref'],
                            self.staged['bad_node']['fwd_node_id']),
                       exception=ShockException)

    def run_error(self, readnames, error, wsname=('fake'), output_name='out',
                  dna_source=None, exception=ValueError):

        test_name = inspect.stack()[1][3]
        print('\n***** starting expected fail test: ' + test_name + ' *****')
        print('    libs: ' + str(readnames))

        if wsname == ('fake'):
            wsname = self.getWsName()

        params = {}
        if (wsname is not None):
            if wsname == 'None':
                params['workspace_name'] = None
            else:
                params['workspace_name'] = wsname

        if (readnames is not None):
            params['read_libraries'] = readnames

        if (output_name is not None):
            params['output_contigset_name'] = output_name

        if not (dna_source is None):
            params['dna_source'] = dna_source

        with self.assertRaises(exception) as context:
            self.getImpl().run_SPAdes(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def run_success(self, readnames, output_name, expected, contig_count=None,
                    dna_source=None):

        test_name = inspect.stack()[1][3]
        print('\n**** starting expected success test: ' + test_name + ' *****')
        print('   libs: ' + str(readnames))

        if not contig_count:
            contig_count = len(expected['contigs'])

        libs = [self.staged[n]['info'][1] for n in readnames]
        assyrefs = sorted(
            [self.make_ref(self.staged[n]['info']) for n in readnames])

        params = {'workspace_name': self.getWsName(),
                  'read_libraries': libs,
                  'output_contigset_name': output_name
                  }

        if not (dna_source is None):
            if dna_source == 'None':
                params['dna_source'] = None
            else:
                params['dna_source'] = dna_source

        ret = self.getImpl().run_SPAdes(self.ctx, params)[0]

        report = self.wsClient.get_objects([{'ref': ret['report_ref']}])[0]
        self.assertEqual('KBaseReport.Report', report['info'][2].split('-')[0])
        self.assertEqual(1, len(report['data']['objects_created']))
        self.assertEqual('Assembled contigs',
                         report['data']['objects_created'][0]['description'])
        self.assertIn('Assembled into ' + str(contig_count) +
                      ' contigs', report['data']['text_message'])
        self.assertEqual(1, len(report['provenance']))
        self.assertEqual(
            assyrefs, sorted(report['provenance'][0]['input_ws_objects']))
        self.assertEqual(
            assyrefs,
            sorted(report['provenance'][0]['resolved_ws_objects']))

        cs_ref = report['data']['objects_created'][0]['ref']
        cs = self.wsClient.get_objects([{'ref': cs_ref}])[0]
        self.assertEqual('KBaseGenomes.ContigSet', cs['info'][2].split('-')[0])
        self.assertEqual(1, len(cs['provenance']))
        self.assertEqual(
            assyrefs, sorted(cs['provenance'][0]['input_ws_objects']))
        self.assertEqual(
            assyrefs, sorted(cs['provenance'][0]['resolved_ws_objects']))
        self.assertEqual(output_name, cs['info'][1])

        cs_fasta_node = cs['data']['fasta_ref']
        self.nodes_to_delete.append(cs_fasta_node)
        header = {"Authorization": "Oauth {0}".format(self.token)}
        fasta_node = requests.get(self.shockURL + '/node/' + cs_fasta_node,
                                  headers=header, allow_redirects=True).json()
        self.assertEqual(expected['fasta_md5'],
                         fasta_node['data']['file']['checksum']['md5'])

        self.assertEqual(contig_count, len(cs['data']['contigs']))
        self.assertEqual(output_name, cs['data']['id'])
        self.assertEqual(output_name, cs['data']['name'])
        self.assertEqual(expected['md5'], cs['data']['md5'])
        self.assertEqual('See provenance', cs['data']['source'])
        self.assertEqual('See provenance', cs['data']['source_id'])

        for i, (exp, got) in enumerate(zip(expected['contigs'],
                                           cs['data']['contigs'])):
            print('Checking contig ' + str(i) + ': ' + exp['name'])
            exp['s_len'] = exp['length']
            got['s_len'] = len(got['sequence'])
            del got['sequence']
            self.assertDictEqual(exp, got)
