
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
 * <p>Original spec-file type: SPAdesParams</p>
 * <pre>
 * Input parameters for running SPAdes.
 * workspace_name - the name of the workspace from which to take input
 *                  and store output.
 * output_contigset_name - the name of the output contigset
 * read_libraries - a list of Illumina PairedEndLibrary files in FASTQ or BAM format.
 * dna_source - (optional) the source of the DNA used for sequencing 'single_cell': DNA
 *                  amplified from a single cell via MDA anything else: Standard
 *                  DNA sample from multiple cells. Default value is None.
 * min_contig_length - (optional) integer to filter out contigs with length < min_contig_length
 *                  from the SPAdes output. Default value is 0 implying no filter.
 * kmer_sizes - (optional) K-mer sizes, Default values: 33, 55, 77, 99, 127
 *                  (all values must be odd, less than 128 and listed in ascending order)
 *                  In the absence of these values, K values are automatically selected.
 * skip_error_correction - (optional) Assembly only (No error correction).
 *                  By default this is disabled.
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "workspace_name",
    "output_contigset_name",
    "read_libraries",
    "dna_source",
    "min_contig_length",
    "kmer_sizes",
    "skip_error_correction"
})
public class SPAdesParams {

    @JsonProperty("workspace_name")
    private java.lang.String workspaceName;
    @JsonProperty("output_contigset_name")
    private java.lang.String outputContigsetName;
    @JsonProperty("read_libraries")
    private List<String> readLibraries;
    @JsonProperty("dna_source")
    private java.lang.String dnaSource;
    @JsonProperty("min_contig_length")
    private java.lang.Long minContigLength;
    @JsonProperty("kmer_sizes")
    private List<Long> kmerSizes;
    @JsonProperty("skip_error_correction")
    private java.lang.Long skipErrorCorrection;
    private Map<java.lang.String, Object> additionalProperties = new HashMap<java.lang.String, Object>();

    @JsonProperty("workspace_name")
    public java.lang.String getWorkspaceName() {
        return workspaceName;
    }

    @JsonProperty("workspace_name")
    public void setWorkspaceName(java.lang.String workspaceName) {
        this.workspaceName = workspaceName;
    }

    public SPAdesParams withWorkspaceName(java.lang.String workspaceName) {
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

    public SPAdesParams withOutputContigsetName(java.lang.String outputContigsetName) {
        this.outputContigsetName = outputContigsetName;
        return this;
    }

    @JsonProperty("read_libraries")
    public List<String> getReadLibraries() {
        return readLibraries;
    }

    @JsonProperty("read_libraries")
    public void setReadLibraries(List<String> readLibraries) {
        this.readLibraries = readLibraries;
    }

    public SPAdesParams withReadLibraries(List<String> readLibraries) {
        this.readLibraries = readLibraries;
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

    public SPAdesParams withDnaSource(java.lang.String dnaSource) {
        this.dnaSource = dnaSource;
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

    public SPAdesParams withMinContigLength(java.lang.Long minContigLength) {
        this.minContigLength = minContigLength;
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

    public SPAdesParams withKmerSizes(List<Long> kmerSizes) {
        this.kmerSizes = kmerSizes;
        return this;
    }

    @JsonProperty("skip_error_correction")
    public java.lang.Long getSkipErrorCorrection() {
        return skipErrorCorrection;
    }

    @JsonProperty("skip_error_correction")
    public void setSkipErrorCorrection(java.lang.Long skipErrorCorrection) {
        this.skipErrorCorrection = skipErrorCorrection;
    }

    public SPAdesParams withSkipErrorCorrection(java.lang.Long skipErrorCorrection) {
        this.skipErrorCorrection = skipErrorCorrection;
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
        return ((((((((((((((((("SPAdesParams"+" [workspaceName=")+ workspaceName)+", outputContigsetName=")+ outputContigsetName)+", readLibraries=")+ readLibraries)+", dnaSource=")+ dnaSource)+", minContigLength=")+ minContigLength)+", kmerSizes=")+ kmerSizes)+", skipErrorCorrection=")+ skipErrorCorrection)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
