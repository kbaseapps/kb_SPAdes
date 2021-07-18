/*
A KBase module: kb_SPAdes
A wrapper for the SPAdes assembler with hybrid features supported.
http://bioinf.spbau.ru/spades

Always runs in careful mode.
Runs 3 threads / CPU.
Maximum memory use is set to available memory - 1G.
Autodetection is used for the PHRED quality offset and k-mer sizes.
A coverage cutoff is not specified.

*/

module kb_SPAdes {

    /* A boolean. 0 = false, anything else = true. */
    typedef int bool;
    
    /* The workspace object name of a PairedEndLibrary file, whether of the
       KBaseAssembly or KBaseFile type.
    */
    typedef string paired_end_lib;

    /* Input parameters for running SPAdes.
    workspace_name - the name of the workspace from which to take input
                     and store output.
    output_contigset_name - the name of the output contigset
    read_libraries - a list of Illumina PairedEndLibrary files in FASTQ or BAM format.
    dna_source - (optional) the source of the DNA used for sequencing 'single_cell': DNA
                     amplified from a single cell via MDA anything else: Standard
                     DNA sample from multiple cells. Default value is None.
    min_contig_length - (optional) integer to filter out contigs with length < min_contig_length
                     from the SPAdes output. Default value is 0 implying no filter.
    kmer_sizes - (optional) K-mer sizes, Default values: 33, 55, 77, 99, 127
                     (all values must be odd, less than 128 and listed in ascending order)
                     In the absence of these values, K values are automatically selected.
    skip_error_correction - (optional) Assembly only (No error correction).
                     By default this is disabled.
    */

    typedef structure {
        string workspace_name;
        string output_contigset_name;
        list<paired_end_lib> read_libraries;
        string dna_source;
        int min_contig_length;
        list<int> kmer_sizes;
        bool skip_error_correction;
    } SPAdesParams;

    /* An X/Y/Z style KBase object reference
    */
    typedef string obj_ref;

    /* parameter groups--define attributes for specifying inputs with YAML data set file (advanced)
       The following attributes are available:

            - orientation ("fr", "rf", "ff")
            - type ("paired-end", "mate-pairs", "hq-mate-pairs", "single", "pacbio", "nanopore", "sanger", "trusted-contigs", "untrusted-contigs")
            - interlaced reads (comma-separated list of files with interlaced reads)
            - left reads (comma-separated list of files with left reads)
            - right reads (comma-separated list of files with right reads)
            - single reads (comma-separated list of files with single reads or unpaired reads from paired library)
            - merged reads (comma-separated list of files with merged reads)

    */
    typedef structure {
        obj_ref lib_ref;
        string orientation;
        string lib_type;
    } ReadsParams;

    typedef structure {
        obj_ref long_reads_ref;
        string long_reads_type;
    } LongReadsParams;


    /*------To run HybridSPAdes 3.13.0 you need at least one library of the following types:------
    1) Illumina paired-end/high-quality mate-pairs/unpaired reads
    2) IonTorrent paired-end/high-quality mate-pairs/unpaired reads
    3) PacBio CCS reads
    Version 3.13.0 of SPAdes supports paired-end reads, mate-pairs and unpaired reads.
    SPAdes can take as input several paired-end and mate-pair libraries simultaneously.

    workspace_name - the name of the workspace from which to take input
                     and store output.
    output_contigset_name - the name of the output contigset
    read_libraries - a list of Illumina or IonTorrent paired-end/high-quality mate-pairs/unpaired reads
    long_reads_libraries - a list of PacBio, Oxford Nanopore Sanger reads and/or additional contigs
    dna_source - the source of the DNA used for sequencing 'single_cell': DNA
                     amplified from a single cell via MDA anything else: Standard
                     DNA sample from multiple cells. Default value is None.
    pipeline_options - a list of string specifying how the SPAdes pipeline should be run
    kmer_sizes - (optional) K-mer sizes, Default values: 21, 33, 55, 77, 99, 127
                     (all values must be odd, less than 128 and listed in ascending order)
                     In the absence of these values, K values are automatically selected.
    min_contig_length - integer to filter out contigs with length < min_contig_length
                     from the HybridSPAdes output. Default value is 0 implying no filter.    
    @optional dna_source
    @optional pipeline_options
    @optional kmer_sizes
    @optional min_contig_length
    */

    typedef structure {
        string workspace_name;
        string output_contigset_name;
        list<ReadsParams> reads_libraries;
        list<LongReadsParams> long_reads_libraries;

        string dna_source;
        list<string> pipeline_options;
        list<int> kmer_sizes;
        int min_contig_length;
        bool create_report;
    } HybridSPAdesParams;

    /* Output parameters for SPAdes run.

    report_name - the name of the KBaseReport.Report workspace object.
    report_ref - the workspace reference of the report.

    */
    typedef structure {
        string report_name;
        string report_ref;
    } SPAdesOutput;
    
    /* Run SPAdes on paired end libraries */
    funcdef run_SPAdes(SPAdesParams params) returns(SPAdesOutput output)
        authentication required;

    /* Run HybridSPAdes on paired end libraries with PacBio CLR and Oxford Nanopore reads*/
    funcdef run_HybridSPAdes(HybridSPAdesParams params) returns(SPAdesOutput output)
        authentication required;

    /* Run SPAdes on paired end libraries for metagenomes */
    funcdef run_metaSPAdes(SPAdesParams params) returns(SPAdesOutput output)
        authentication required;
};

