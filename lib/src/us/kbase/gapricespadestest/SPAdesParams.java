
package us.kbase.gapricespadestest;

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
 * string workspace_name - the name of the workspace from which to take
 *    input and store output.
 * string output_contigset_name - the name of the output contigset
 * list<paired_end_lib> read_libraries - Illumina PairedEndLibrary files
 *     to assemble.
 * string dna_source - the source of the DNA used for sequencing
 *     'single_cell': DNA amplified from a single cell via MDA
 *     'metagenome': Metagenomic data
 *     anything else: Standard DNA sample from multiple cells
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "workspace_name",
    "output_contigset_name",
    "read_libraries",
    "dna_source"
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
        return ((((((((((("SPAdesParams"+" [workspaceName=")+ workspaceName)+", outputContigsetName=")+ outputContigsetName)+", readLibraries=")+ readLibraries)+", dnaSource=")+ dnaSource)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
