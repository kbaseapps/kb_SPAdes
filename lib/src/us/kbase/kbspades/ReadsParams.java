
package us.kbase.kbspades;

import java.util.HashMap;
import java.util.Map;
import javax.annotation.Generated;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


/**
 * <p>Original spec-file type: ReadsParams</p>
 * <pre>
 * parameter groups--define attributes for specifying inputs with YAML data set file (advanced)
 * The following attributes are available:
 *      - orientation ("fr", "rf", "ff")
 *      - type ("paired-end", "mate-pairs", "hq-mate-pairs", "single", "pacbio", "nanopore", "sanger", "trusted-contigs", "untrusted-contigs")
 *      - interlaced reads (comma-separated list of files with interlaced reads)
 *      - left reads (comma-separated list of files with left reads)
 *      - right reads (comma-separated list of files with right reads)
 *      - single reads (comma-separated list of files with single reads or unpaired reads from paired library)
 *      - merged reads (comma-separated list of files with merged reads)
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "lib_ref",
    "orientation",
    "lib_type"
})
public class ReadsParams {

    @JsonProperty("lib_ref")
    private String libRef;
    @JsonProperty("orientation")
    private String orientation;
    @JsonProperty("lib_type")
    private String libType;
    private Map<String, Object> additionalProperties = new HashMap<String, Object>();

    @JsonProperty("lib_ref")
    public String getLibRef() {
        return libRef;
    }

    @JsonProperty("lib_ref")
    public void setLibRef(String libRef) {
        this.libRef = libRef;
    }

    public ReadsParams withLibRef(String libRef) {
        this.libRef = libRef;
        return this;
    }

    @JsonProperty("orientation")
    public String getOrientation() {
        return orientation;
    }

    @JsonProperty("orientation")
    public void setOrientation(String orientation) {
        this.orientation = orientation;
    }

    public ReadsParams withOrientation(String orientation) {
        this.orientation = orientation;
        return this;
    }

    @JsonProperty("lib_type")
    public String getLibType() {
        return libType;
    }

    @JsonProperty("lib_type")
    public void setLibType(String libType) {
        this.libType = libType;
    }

    public ReadsParams withLibType(String libType) {
        this.libType = libType;
        return this;
    }

    @JsonAnyGetter
    public Map<String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(String name, Object value) {
        this.additionalProperties.put(name, value);
    }

    @Override
    public String toString() {
        return ((((((((("ReadsParams"+" [libRef=")+ libRef)+", orientation=")+ orientation)+", libType=")+ libType)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
