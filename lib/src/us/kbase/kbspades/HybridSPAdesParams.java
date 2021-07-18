
package us.kbase.kbspades;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.annotation.Generated;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


/**
 * <p>Original spec-file type: HybridSPAdesParams</p>
 * <pre>
 * ------To run HybridSPAdes 3.13.0 you need at least one library of the following types:------
 *  1) Illumina paired-end/high-quality mate-pairs/unpaired reads
 *  2) IonTorrent paired-end/high-quality mate-pairs/unpaired reads
 *  3) PacBio CCS reads
 * Version 3.13.0 of SPAdes supports paired-end reads, mate-pairs and unpaired reads.
 * SPAdes can take as input several paired-end and mate-pair libraries simultaneously.
 * workspace_name - the name of the workspace from which to take input
 *                  and store output.
 * output_contigset_name - the name of the output contigset
 * read_libraries - a list of Illumina or IonTorrent paired-end/high-quality mate-pairs/unpaired reads
 * long_reads_libraries - a list of PacBio, Oxford Nanopore Sanger reads and/or additional contigs
 * dna_source - the source of the DNA used for sequencing 'single_cell': DNA
 *                  amplified from a single cell via MDA anything else: Standard
 *                  DNA sample from multiple cells. Default value is None.
 * pipeline_options - a list of string specifying how the SPAdes pipeline should be run
 * kmer_sizes - (optional) K-mer sizes, Default values: 21, 33, 55, 77, 99, 127
 *                  (all values must be odd, less than 128 and listed in ascending order)
 *                  In the absence of these values, K values are automatically selected.
 * min_contig_length - integer to filter out contigs with length < min_contig_length
 *                  from the HybridSPAdes output. Default value is 0 implying no filter.    
 * @optional dna_source
 * @optional pipeline_options
 * @optional kmer_sizes
 * @optional min_contig_length
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "workspace_name",
    "output_contigset_name",
    "reads_libraries",
    "long_reads_libraries",
    "dna_source",
    "pipeline_options",
    "kmer_sizes",
    "min_contig_length",
    "create_report"
})
public class HybridSPAdesParams {

    @JsonProperty("workspace_name")
    private java.lang.String workspaceName;
    @JsonProperty("output_contigset_name")
    private java.lang.String outputContigsetName;
    @JsonProperty("reads_libraries")
    private List<ReadsParams> readsLibraries;
    @JsonProperty("long_reads_libraries")
    private List<LongReadsParams> longReadsLibraries;
    @JsonProperty("dna_source")
    private java.lang.String dnaSource;
    @JsonProperty("pipeline_options")
    private List<String> pipelineOptions;
    @JsonProperty("kmer_sizes")
    private List<Long> kmerSizes;
    @JsonProperty("min_contig_length")
    private java.lang.Long minContigLength;
    @JsonProperty("create_report")
    private java.lang.Long createReport;
    private Map<java.lang.String, Object> additionalProperties = new HashMap<java.lang.String, Object>();

    @JsonProperty("workspace_name")
    public java.lang.String getWorkspaceName() {
        return workspaceName;
    }

    @JsonProperty("workspace_name")
    public void setWorkspaceName(java.lang.String workspaceName) {
        this.workspaceName = workspaceName;
    }

    public HybridSPAdesParams withWorkspaceName(java.lang.String workspaceName) {
        this.workspaceName = workspaceName;
        return this;
    }

    @JsonProperty("output_contigset_name")
    public java.lang.String getOutputContigsetName() {
        return outputContigsetName;
    }

    @JsonProperty("output_contigset_name")
    public void setOutputContigsetName(java.lang.String outputContigsetName) {
        this.outputContigsetName = outputContigsetName;
    }

    public HybridSPAdesParams withOutputContigsetName(java.lang.String outputContigsetName) {
        this.outputContigsetName = outputContigsetName;
        return this;
    }

    @JsonProperty("reads_libraries")
    public List<ReadsParams> getReadsLibraries() {
        return readsLibraries;
    }

    @JsonProperty("reads_libraries")
    public void setReadsLibraries(List<ReadsParams> readsLibraries) {
        this.readsLibraries = readsLibraries;
    }

    public HybridSPAdesParams withReadsLibraries(List<ReadsParams> readsLibraries) {
        this.readsLibraries = readsLibraries;
        return this;
    }

    @JsonProperty("long_reads_libraries")
    public List<LongReadsParams> getLongReadsLibraries() {
        return longReadsLibraries;
    }

    @JsonProperty("long_reads_libraries")
    public void setLongReadsLibraries(List<LongReadsParams> longReadsLibraries) {
        this.longReadsLibraries = longReadsLibraries;
    }

    public HybridSPAdesParams withLongReadsLibraries(List<LongReadsParams> longReadsLibraries) {
        this.longReadsLibraries = longReadsLibraries;
        return this;
    }

    @JsonProperty("dna_source")
    public java.lang.String getDnaSource() {
        return dnaSource;
    }

    @JsonProperty("dna_source")
    public void setDnaSource(java.lang.String dnaSource) {
        this.dnaSource = dnaSource;
    }

    public HybridSPAdesParams withDnaSource(java.lang.String dnaSource) {
        this.dnaSource = dnaSource;
        return this;
    }

    @JsonProperty("pipeline_options")
    public List<String> getPipelineOptions() {
        return pipelineOptions;
    }

    @JsonProperty("pipeline_options")
    public void setPipelineOptions(List<String> pipelineOptions) {
        this.pipelineOptions = pipelineOptions;
    }

    public HybridSPAdesParams withPipelineOptions(List<String> pipelineOptions) {
        this.pipelineOptions = pipelineOptions;
        return this;
    }

    @JsonProperty("kmer_sizes")
    public List<Long> getKmerSizes() {
        return kmerSizes;
    }

    @JsonProperty("kmer_sizes")
    public void setKmerSizes(List<Long> kmerSizes) {
        this.kmerSizes = kmerSizes;
    }

    public HybridSPAdesParams withKmerSizes(List<Long> kmerSizes) {
        this.kmerSizes = kmerSizes;
        return this;
    }

    @JsonProperty("min_contig_length")
    public java.lang.Long getMinContigLength() {
        return minContigLength;
    }

    @JsonProperty("min_contig_length")
    public void setMinContigLength(java.lang.Long minContigLength) {
        this.minContigLength = minContigLength;
    }

    public HybridSPAdesParams withMinContigLength(java.lang.Long minContigLength) {
        this.minContigLength = minContigLength;
        return this;
    }

    @JsonProperty("create_report")
    public java.lang.Long getCreateReport() {
        return createReport;
    }

    @JsonProperty("create_report")
    public void setCreateReport(java.lang.Long createReport) {
        this.createReport = createReport;
    }

    public HybridSPAdesParams withCreateReport(java.lang.Long createReport) {
        this.createReport = createReport;
        return this;
    }

    @JsonAnyGetter
    public Map<java.lang.String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(java.lang.String name, Object value) {
        this.additionalProperties.put(name, value);
    }

    @Override
    public java.lang.String toString() {
        return ((((((((((((((((((((("HybridSPAdesParams"+" [workspaceName=")+ workspaceName)+", outputContigsetName=")+ outputContigsetName)+", readsLibraries=")+ readsLibraries)+", longReadsLibraries=")+ longReadsLibraries)+", dnaSource=")+ dnaSource)+", pipelineOptions=")+ pipelineOptions)+", kmerSizes=")+ kmerSizes)+", minContigLength=")+ minContigLength)+", createReport=")+ createReport)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
