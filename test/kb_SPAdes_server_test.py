from __future__ import print_function
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
from ReadsUtils.baseclient import ServerError
from ReadsUtils.ReadsUtilsClient import ReadsUtils
from kb_SPAdes.kb_SPAdesServer import MethodContext
from pprint import pprint
import shutil
import inspect
from kb_SPAdes.GenericClient import GenericClient


class gaprice_SPAdesTest(unittest.TestCase):

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
        cls.wsURL = cls.cfg['workspace-url']
        cls.shockURL = cls.cfg['shock-url']
        cls.hs = HandleService(url=cls.cfg['handle-service-url'],
                               token=cls.token)
        cls.wsClient = workspaceService(cls.wsURL, token=cls.token)
        wssuffix = int(time.time() * 1000)
        wsName = "test_kb_SPAdes_" + str(wssuffix)
        cls.wsinfo = cls.wsClient.create_workspace({'workspace': wsName})
        print('created workspace ' + cls.getWsName())
        cls.serviceImpl = kb_SPAdes(cls.cfg)
        cls.readUtilsImpl = ReadsUtils(cls.callbackURL, token=cls.token)
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
    def upload_reads(cls, wsobjname, object_body, fwd_reads,
                     rev_reads=None, single_end=False, sequencing_tech='Illumina',
                     single_genome='1'):

        ob = dict(object_body)  # copy
        ob['sequencing_tech'] = sequencing_tech
#        ob['single_genome'] = single_genome
        ob['wsname'] = cls.getWsName()
        ob['name'] = wsobjname
        if single_end or rev_reads:
            ob['interleaved']= 0
        else:
            ob['interleaved']= 1
        print('\n===============staging data for object ' + wsobjname +
              '================')
        print('uploading forward reads file ' + fwd_reads['file'])
        fwd_id, fwd_handle_id, fwd_md5, fwd_size = \
            cls.upload_file_to_shock_and_get_handle(fwd_reads['file'])

        ob['fwd_id']= fwd_id
        rev_id = None
        rev_handle_id = None
        if rev_reads:
            print('uploading reverse reads file ' + rev_reads['file'])
            rev_id, rev_handle_id, rev_md5, rev_size = \
                cls.upload_file_to_shock_and_get_handle(rev_reads['file'])
            ob['rev_id']= rev_id
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
        cls.upload_reads('pacbio', {'single_genome': 1},
                            pacbio_reads, single_end=True, sequencing_tech="PacBio CLR")
        cls.upload_reads('pacbioccs', {'single_genome': 1},
                            pacbio_ccs_reads, single_end=True, sequencing_tech="PacBio CCS")
        cls.upload_reads('iontorrent', {'single_genome': 1},
                            iontorrent_reads, single_end=True, sequencing_tech="IonTorrent")
        cls.upload_reads('meta', {'single_genome': 0}, fwd_reads,
                            rev_reads=rev_reads)
        cls.upload_reads('meta2', {'single_genome': 0}, fwd_reads,
                            rev_reads=rev_reads)
        cls.upload_reads('meta_single_end', {'single_genome': 0}, fwd_reads, single_end=True)
        cls.upload_reads('reads_out', {'read_orientation_outward': 1},
                            int_reads)
        cls.upload_assembly('frbasic_kbassy', {}, fwd_reads,
                            rev_reads=rev_reads, kbase_assy=True)
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

    def test_fr_pair_kbfile(self):

        self.run_success(
            ['frbasic'], 'frbasic_out',
            contig_count=2)

    def test_fr_pair_kbassy(self):

        self.run_success(
            ['frbasic_kbassy'], 'frbasic_kbassy_out',
            contig_count=2)

    def test_interlaced_kbfile(self):

        self.run_success(
            ['intbasic'], 'intbasic_out')

    def test_metagenome_kbfile(self):
        self.run_success(
            ['meta'], 'metabasic_out',
            contig_count=2, dna_source='metagenomic')

    def test_metagenome_multiple(self):
        self.run_error(['meta', 'meta2'],
                       'Metagenome assembly requires that one ' +
                       'and only one paired end library as input. ' +
                       '2 libraries detected.',
                       dna_source='metagenomic')

    def test_metagenome_single_end(self):
        self.run_error(['meta_single_end'],
                       'Metagenome assembly requires that one ' +
                       'and only one paired end library as input.',
                       dna_source='metagenomic')

    def test_plasmid_kbfile(self):
        self.run_success(
            ['plasmid_reads'], 'plasmid_out',
            contig_count=1, dna_source='plasmid')

    def test_plasmid_multiple(self):
        self.run_error(['plasmid_reads', 'frbasic'],
                       'Plasmid assembly requires that one ' +
                       'and only one library as input. ' +
                       '2 libraries detected.',
                       dna_source='plasmid')

    def test_interlaced_kbassy(self):

        self.run_success(
            ['intbasic_kbassy'], 'intbasic_kbassy_out',
            contig_count=1479, dna_source='')

    def test_multiple(self):
        self.run_success(
            ['intbasic_kbassy', 'frbasic'], 'multiple_out',
            dna_source='None')

    def test_multiple_pacbio_illumina(self):
        self.run_success(
            ['intbasic_kbassy', 'pacbio'], 'pacbio_multiple_out',
            dna_source='None')

    def test_multiple_pacbio_single(self):
        self.run_success(
            ['single_end', 'pacbio'], 'pacbio_single_out',
            dna_source='None')

    def test_multiple_single(self):
        self.run_success(
            ['single_end', 'single_end2'], 'multiple_single_out',
            dna_source='None')


    def test_iontorrent_alone(self):
        self.run_non_deterministic_success(
            ['iontorrent'], 'iontorrent_alone_out',
            dna_source='None')

    def test_multiple_iontorrent_illumina(self):
        self.run_error(['intbasic_kbassy', 'iontorrent'],
                       'Both IonTorrent and Illumina read libraries exist. SPAdes ' +
                       'can not assemble them together.')

    def test_pacbio_alone(self):
        self.run_error(['pacbio'],
                       'Per SPAdes requirements : If doing PacBio CLR reads, you must also ' +
                       'supply at least one paired end or single end reads library')

    def test_pacbioccs_alone(self):
        self.run_success(
            ['pacbioccs'], 'pacbioccs_alone_out',
            dna_source='None')

    def test_multiple_pacbioccs_illumina(self):
        self.run_success(
            ['intbasic_kbassy', 'pacbioccs'], 'pacbioccs_multiple_out',
            dna_source='None')

    def test_single_reads(self):
        self.run_success(
            ['single_end'], 'single_out',
            dna_source='None')

    def test_multiple_bad(self):
        # Testing where input reads have different phred types (33 and 64)
        self.run_error(['intbasic64', 'frbasic'],
                       ('The set of Reads objects passed in have reads that have different phred ' +
                        'type scores. SPAdes does not support assemblies of reads with different ' +
                        'phred type scores.\nThe following read objects have ' +
                        'phred 33 scores : {}/frbasic.\n' +
                        'The following read objects have phred 64 scores : ' +
                        '{}/intbasic64').format(self.getWsName(), self.getWsName()),
                       exception=ValueError)
    
    def test_single_cell(self):

        self.run_success(
            ['frbasic'], 'single_cell_out',
            dna_source='single_cell')

    def test_meta_kmer_sizes(self):

        self.run_success(
            ['frbasic'], 'frbasic_out',
            contig_count=2, dna_source='metagenomic',
            kmer_sizes=[33, 55, 77, 99, 127])

    def test_invalid_kmer_sizes(self):

        self.run_error(
            ['frbasic'], 'Insufficient number of k-mer sizes: Expected atleast 3 values: 33',
            kmer_sizes=[33])

    def test_invalid_min_contig_length(self):

        self.run_error(
            ['frbasic'], 'min_contig_length must be of type int', min_contig_length='not an int!')
    
    def test_no_workspace_param(self):

        self.run_error(
            ['foo'], 'workspace_name parameter is required', wsname=None)

    def test_bad_workspace_name(self):

        self.run_error(['foo'], 'Invalid workspace name bad|name',
                       wsname='bad|name')

    def test_non_extant_workspace(self):

        self.run_error(
            ['foo'], 'Object foo cannot be accessed: No workspace with name ' +
            'Ireallyhopethisworkspacedoesntexistorthistestwillfail exists',
            wsname='Ireallyhopethisworkspacedoesntexistorthistestwillfail',
            exception=WorkspaceError)

    # TEST REMOVED SINCE FROM THE UI IT IS A REFERENCE (Old logic in Impl broke UI)
    # def test_bad_lib_name(self):

    #   self.run_error(['bad&name'], 'Invalid workspace object name bad&name')

    def test_no_libs_param(self):

        self.run_error(None, 'read_libraries parameter is required')

    def test_no_libs_list(self):

        self.run_error('foo', 'read_libraries must be a list')

    def test_non_extant_lib(self):

        self.run_error(
            ['foo'],
            ('No object with name foo exists in workspace {} ' +
             '(name {})').format(str(self.wsinfo[0]), self.wsinfo[1]),
            exception=WorkspaceError)

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

    # def test_inconsistent_metagenomics_1(self):

    #     self.run_error(
    #         ['intbasic'],
    #         'Reads object ' + self.getWsName() + '/intbasic (' +
    #         self.staged['intbasic']['ref'] +
    #         ') is marked as containing dna from a single genome but the ' +
    #         'assembly method was specified as metagenomic',
    #         dna_source='metagenomic')

    def test_inconsistent_metagenomics_2(self):

        self.run_error(
            ['meta'],
            'Reads object ' + self.getWsName() + '/meta (' +
            self.staged['meta']['ref'] +
            ') is marked as containing metagenomic data but the assembly ' +
            'method was not specified as metagenomic')

    def test_outward_reads(self):

        self.run_error(
            ['reads_out'],
            'Reads object ' + self.getWsName() + '/reads_out (' +
            self.staged['reads_out']['ref'] +
            ') is marked as having outward oriented reads, which SPAdes ' +
            'does not support.')

    def test_bad_module(self):

        self.run_error(['empty'],
                       'Invalid type for object ' +
                       self.staged['empty']['ref'] + ' (empty). Only the ' +
                       'types KBaseAssembly.PairedEndLibrary and ' +
                       'KBaseFile.PairedEndLibrary are supported')

    def test_bad_shock_filename(self):

        self.run_error(
            ['bad_shk_name'],
            ('Shock file name is illegal: small.forward.bad. Expected FASTQ ' +
             'file. Reads object bad_shk_name ({}). Shock node ' +
             '{}').format(self.staged['bad_shk_name']['ref'],
                          self.staged['bad_shk_name']['fwd_node_id']),
            exception=ServerError)

    def test_bad_handle_filename(self):

        self.run_error(
            ['bad_file_name'],
            ('Handle file name from reads Workspace object is illegal: file.terrible. ' +
             'Expected FASTQ file. Reads object bad_file_name ({}). Shock node ' +
             '{}').format(self.staged['bad_file_name']['ref'],
                          self.staged['bad_file_name']['fwd_node_id']),
            exception=ServerError)

    def test_bad_file_type(self):

        self.run_error(
            ['bad_file_type'],
            ('File type from reads Workspace object is illegal: .xls. Expected ' +
             'FASTQ file. Reads object bad_file_type ({}). Shock node ' +
             '{}').format(self.staged['bad_file_type']['ref'],
                          self.staged['bad_file_type']['fwd_node_id']),
            exception=ServerError)

    def test_bad_shock_node(self):

        self.run_error(['bad_node'],
                       ('Handle error for object {}: The Handle Manager ' +
                        'reported a problem while attempting to set Handle ACLs: ' +
                        'Unable to set acl(s) on handles ' +
                        '{}').format(
                            self.staged['bad_node']['ref'],
                            self.staged['bad_node']['fwd_handle_id']),
                       exception=ServerError)

#     def test_provenance(self):

#         frbasic = 'frbasic'
#         ref = self.make_ref(self.staged[frbasic]['info'])
#         gc = GenericClient(self.callbackURL, use_url_lookup=False)
#         gc.sync_call('CallbackServer.set_provenance',
#                      [{'service': 'myserv',
#                        'method': 'mymeth',
#                        'service_ver': '0.0.2',
#                        'method_params': ['foo', 'bar', 'baz'],
#                        'input_ws_objects': [ref]
#                        }]
#                      )

#         params = {'workspace_name': self.getWsName(),
#                   'read_libraries': [frbasic],
#                   'output_contigset_name': 'foo'
#                   }

#         ret = self.getImpl().run_SPAdes(self.ctx, params)[0]
#         report = self.wsClient.get_objects([{'ref': ret['report_ref']}])[0]
#         assembly_ref = report['data']['objects_created'][0]['ref']
#         assembly = self.wsClient.get_objects([{'ref': assembly_ref}])[0]

#         rep_prov = report['provenance']
#         assembly_prov = assembly['provenance']
#         self.assertEqual(len(rep_prov), 1)
# #        self.assertEqual(len(assembly_prov), 2)
# #       rep_prov = rep_prov[0]
# #       assembly_prov = assembly_prov[0]
# #       for p in [rep_prov, assembly_prov]:
# #            self.assertEqual(p['service'], 'myserv')
# #            self.assertEqual(p['method'], 'mymeth')
# #            self.assertEqual(p['service_ver'], '0.0.2')
# #            self.assertEqual(p['method_params'], ['foo', 'bar', 'baz'])
# #            self.assertEqual(p['input_ws_objects'], [ref])
# #            sa = p['subactions']
# #            self.assertEqual(len(sa), 1)
# #            sa = sa[0]
# #            self.assertEqual(
# #                sa['name'],
# #                'kb_read_library_to_file')
# #            self.assertEqual(
# #                sa['code_url'],
# #                'https://github.com/MrCreosote/kb_read_library_to_file')
# # don't check ver or commit since they can change from run to run

    def run_error(self, readnames, error, wsname=('fake'), output_name='out',
                  dna_source=None, min_contig_length=0, exception=ValueError,
                  kmer_sizes=None, skip_error_correction=0):

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

        params['min_contig_length'] = min_contig_length
        params['kmer_sizes'] = kmer_sizes
        params['skip_error_correction'] = skip_error_correction

        with self.assertRaises(exception) as context:
            self.getImpl().run_SPAdes(self.ctx, params)
        self.assertEqual(error, str(context.exception.message))

    def run_success(self, readnames, output_name, expected=None, contig_count=None,
                    min_contig_length=0, dna_source=None,
                    kmer_sizes=None, skip_error_correction=0):

        test_name = inspect.stack()[1][3]
        print('\n**** starting expected success test: ' + test_name + ' *****')
        print('   libs: ' + str(readnames))

        print("READNAMES: " + str(readnames))
        print("STAGED: " + str(self.staged))

        libs = [self.staged[n]['info'][1] for n in readnames]
#        assyrefs = sorted(
#            [self.make_ref(self.staged[n]['info']) for n in readnames])

        params = {'workspace_name': self.getWsName(),
                  'read_libraries': libs,
                  'output_contigset_name': output_name,
                  'min_contig_length': min_contig_length,
                  'kmer_sizes': kmer_sizes,
                  'skip_error_correction': skip_error_correction
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
        if not (contig_count):
          self.assertIn('Assembled into ', report['data']['text_message'])
        else:
          self.assertIn('Assembled into ' + str(contig_count) +
                      ' contigs', report['data']['text_message'])

        print("PROVENANCE: " + str(report['provenance']))
        self.assertEqual(1, len(report['provenance']))
        # PERHAPS ADD THESE TESTS BACK IN THE FUTURE, BUT AssemblyUtils and this
        # would need to pass in the extra provenance information
#        self.assertEqual(
#            assyrefs, sorted(report['provenance'][0]['input_ws_objects']))
#        self.assertEqual(
#            assyrefs,
#            sorted(report['provenance'][0]['resolved_ws_objects']))

        assembly_ref = report['data']['objects_created'][0]['ref']
        assembly = self.wsClient.get_objects([{'ref': assembly_ref}])[0]
        # print("ASSEMBLY OBJECT:")
        self.assertEqual('KBaseGenomeAnnotations.Assembly', assembly['info'][2].split('-')[0])
        self.assertEqual(1, len(assembly['provenance']))
        # PERHAPS ADD THESE TESTS BACK IN THE FUTURE, BUT AssemblyUtils and this
        # would need to pass in the extra provenance information
#        self.assertEqual(
#            assyrefs, sorted(assembly['provenance'][0]['input_ws_objects']))
#        self.assertEqual(
#            assyrefs, sorted(assembly['provenance'][0]['resolved_ws_objects']))
        self.assertEqual(output_name, assembly['info'][1])

#        handle_id = assembly['data']['fasta_handle_ref']
#        print("HANDLE ID:" + handle_id)
#        handle_ids_list = list()
#        handle_ids_list.append(handle_id)
#        print("HANDLE IDS:" + str(handle_ids_list))
#        temp_handle_info = self.hs.hids_to_handles(handle_ids_list)
        temp_handle_info = self.hs.hids_to_handles([assembly['data']['fasta_handle_ref']])
        print("HANDLE OBJECT:")
        pprint(temp_handle_info)
        assembly_fasta_node = temp_handle_info[0]['id']
        self.nodes_to_delete.append(assembly_fasta_node)
        header = {"Authorization": "Oauth {0}".format(self.token)}
        fasta_node = requests.get(self.shockURL + '/node/' + assembly_fasta_node,
                                  headers=header, allow_redirects=True).json()
        
        if not (contig_count is None):
          self.assertEqual(contig_count, len(assembly['data']['contigs']))

        self.assertEqual(output_name, assembly['data']['assembly_id'])
        # self.assertEqual(output_name, assembly['data']['name']) #name key doesnt seem to exist
        
        if not (expected is None):
          self.assertEqual(expected['fasta_md5'],
                         fasta_node['data']['file']['checksum']['md5'])

          self.assertEqual(expected['md5'], assembly['data']['md5'])

          self.assertIn('Assembled into ' + str(contig_count) +
                      ' contigs', report['data']['text_message'])

          for exp_contig in expected['contigs']:
              if exp_contig['id'] in assembly['data']['contigs']:
                  obj_contig = assembly['data']['contigs'][exp_contig['id']]
                  self.assertEqual(exp_contig['name'], obj_contig['name'])
                  self.assertEqual(exp_contig['md5'], obj_contig['md5'])
                  self.assertEqual(exp_contig['length'], obj_contig['length'])
              else:
                  # Hacky way to do this, but need to see all the contig_ids
                  # They changed because the SPAdes version changed and
                  # Need to see them to update the tests accordingly.
                  # If code gets here this test is designed to always fail, but show results.
                  self.assertEqual(str(assembly['data']['contigs']), "BLAH")


    def run_non_deterministic_success(self, readnames, output_name,
                    dna_source=None):

        test_name = inspect.stack()[1][3]
        print('\n**** starting expected success test: ' + test_name + ' *****')
        print('   libs: ' + str(readnames))

        print("READNAMES: " + str(readnames))
        print("STAGED: " + str(self.staged))

        libs = [self.staged[n]['info'][1] for n in readnames]

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
        self.assertIn('Assembled into ', report['data']['text_message'])
        self.assertIn('contigs', report['data']['text_message'])

        assembly_ref = report['data']['objects_created'][0]['ref']
        assembly = self.wsClient.get_objects([{'ref': assembly_ref}])[0]
        self.assertEqual('KBaseGenomeAnnotations.Assembly', assembly['info'][2].split('-')[0])
        self.assertEqual(output_name, assembly['info'][1])
