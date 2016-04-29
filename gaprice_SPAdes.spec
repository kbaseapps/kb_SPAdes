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

module gaprice_SPAdes {

    /* A boolean. 0 = false, anything else = true. */
    typedef int bool;
    
    /* The workspace object name of a PairedEndLibrary file, whether of the
       KBaseAssembly or KBaseFile type.
    */
    typedef string paired_end_lib;
    
    /* Input parameters for running SPAdes.
        string workspace_name - the name of the workspace from which to take
           input and store output.
        string output_contigset_name - the name of the output contigset
        list<paired_end_lib> read_libraries - Illumina PairedEndLibrary files
            to assemble.
        string dna_source - the source of the DNA used for sequencing
            'single_cell': DNA amplified from a single cell via MDA
            'metagenome': Metagenomic data
            anything else: Standard DNA sample from multiple cells
        
    */
    typedef structure {
        string workspace_name;
        string output_contigset_name;
        list<paired_end_lib> read_libraries;
        string dna_source;
    } SPAdesParams;
    
    /* Output parameters for SPAdes run.
        string report_name - the name of the KBaseReport.Report workspace
            object.
        string report_ref - the workspace reference of the report.
    */
    typedef structure {
        string report_name;
        string report_ref;
    } SPAdesOutput;
    
    /* Run SPAdes on paired end libraries */
    funcdef run_SPAdes(SPAdesParams params) returns(SPAdesOutput output)
        authentication required;
};