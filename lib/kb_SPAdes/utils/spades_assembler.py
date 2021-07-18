import os
import re
import time
import uuid

from installed_clients.AssemblyUtilClient import AssemblyUtil
from kb_SPAdes.utils.spades_utils import SPAdesUtils


def log(message, prefix_newline=False):
    """Logging function, provides a hook to suppress or redirect log messages."""
    print(('\n' if prefix_newline else '') + '{0:.2f}'.format(time.time()) + ': ' + str(message))


def mkdir_p(path):
    """
    mkdir_p: make directory for given path
    """
    if not path:
        return
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == os.errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class SPAdesAssembler(object):
    INVALID_WS_OBJ_NAME_RE = re.compile('[^\\w\\|._-]')
    INVALID_WS_NAME_RE = re.compile('[^\\w:._-]')

    PARAM_IN_CS_NAME = 'output_contigset_name'
    SPAdes_PROJECT_DIR = 'spades_project_dir'
    SPAdes_final_scaffolds = 'scaffolds.fasta'  # resulting scaffolds sequences

    def __init__(self, config, provenance):
        """
        __init__: construct SPAdesAssembler
        """
        # BEGIN_CONSTRUCTOR
        self.workspace_url = config["workspace-url"]
        self.callback_url = config["SDK_CALLBACK_URL"]
        self.token = config["KB_AUTH_TOKEN"]
        self.provenance = provenance

        self.au = AssemblyUtil(self.callback_url)

        self.scratch = os.path.join(config['scratch'], str(uuid.uuid4()))
        mkdir_p(self.scratch)

        self.spades_version = 'SPADES-' + os.environ['SPADES_VERSION']
        self.proj_dir = self._create_proj_dir(self.scratch)
        self.s_utils = SPAdesUtils(self.proj_dir, config)
        # END_CONSTRUCTOR
        pass

    def _save_assembly(self, params):
        """
        _save_assembly: save the assembly to KBase and, if everything has gone well, create a report
        """
        returnVal = {
            "report_ref": None,
            "report_name": None
        }

        wsname = params['workspace_name']
        fa_file_dir = self._find_file_dir(self.proj_dir, self.SPAdes_final_scaffolds)

        if fa_file_dir != '':
            log('Found the directory {} that hosts the contig fasta file: {}'.format(
                    fa_file_dir, self.SPAdes_final_scaffolds))
            fa_file_path = os.path.join(fa_file_dir, self.SPAdes_final_scaffolds)

            log("Load assembly from fasta file {}...".format(fa_file_path))
            report_file = self.SPAdes_final_scaffolds
            min_ctg_length = params.get('min_contig_length', 0)
            if min_ctg_length > 0:
                self.s_utils.save_assembly(fa_file_path, wsname,
                                           params[self.PARAM_IN_CS_NAME],
                                           min_ctg_length)
                report_file += '.filtered.fa'
            else:
                self.s_utils.save_assembly(fa_file_path, wsname,
                                           params[self.PARAM_IN_CS_NAME])

            if params['create_report'] == 1:
                report_name, report_ref = self.s_utils.generate_report(
                                        report_file, params, fa_file_dir, wsname)
                returnVal = {'report_name': report_name,
                             'report_ref': report_ref}
        return returnVal

    def _find_file_dir(self, search_dir, search_file_name):
        """
        _find_file_dir: search a given directory to find immediate dir that hosts the given file
        """
        for dirName, subdirList, fileList in os.walk(search_dir):
            for fname in fileList:
                if fname == search_file_name:
                    log('Found file {} in {}'.format(fname, dirName))
                    return dirName
        log('Could not find file {}!'.format(search_file_name))
        return ''

    def _create_proj_dir(self, home_dir):
        """
        _create_proj_dir: creating the project directory for SPAdes
        """
        prjdir = os.path.join(home_dir, self.SPAdes_PROJECT_DIR)
        mkdir_p(prjdir)
        return prjdir

    def run_hybrid_spades(self, params):
        """
        run_hybrid_spades: breakdown steps of SPAdes assembling process
        """
        # 1. validate & process the input parameters
        validated_params = self.s_utils.check_spades_params(params)
        assemble_ok = -1

        # 2: retrieve the reads data from input paramete
        hybrid_reads_info = self.s_utils.get_hybrid_reads_info(validated_params)
        if hybrid_reads_info:  # UNPACKS the reads_info
            (sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs) = \
                hybrid_reads_info

            # 3. create the yaml input data set file
            yaml_file = self.s_utils.construct_yaml_dataset_file(
                sgl_rds, pe_rds, mp_rds, pb_ccs, pb_clr, np_rds, sgr_rds, tr_ctgs, ut_ctgs)

            # 4. run the spades.py against the yaml file
            if os.path.isfile(yaml_file):
                basic_opts = validated_params.get('basic_options', None)
                pipleline_opts = validated_params.get('pipeline_options', None)
                km_sizes = validated_params.get('kmer_sizes', None)
                dna_src = validated_params.get('dna_source', None)
                assemble_ok = self.s_utils.run_assemble(yaml_file, km_sizes, dna_src,
                                                        basic_opts, pipleline_opts)

        # 5. save the assembly to KBase and, if everything has gone well, create a report
        if assemble_ok == 0:
            return self._save_assembly(validated_params)
        else:
            log("run_hybrid_spades failed.")
            return {"report_ref": None, "report_name": None}
