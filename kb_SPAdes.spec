/*
A KBase module: gaprice_SPAdes
Simple wrapper for the SPAdes assembler.
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
    output_contigset_name - the name of the output contigset list<paired_end_lib>
                     read_libraries - Illumina PairedEndLibrary files to assemble.
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
};