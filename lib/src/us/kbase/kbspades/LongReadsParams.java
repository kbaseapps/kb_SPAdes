
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
 * <p>Original spec-file type: LongReadsParams</p>
 * 
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "long_reads_ref",
    "long_reads_type"
})
public class LongReadsParams {

    @JsonProperty("long_reads_ref")
    private String longReadsRef;
    @JsonProperty("long_reads_type")
    private String longReadsType;
    private Map<String, Object> additionalProperties = new HashMap<String, Object>();

    @JsonProperty("long_reads_ref")
    public String getLongReadsRef() {
        return longReadsRef;
    }

    @JsonProperty("long_reads_ref")
    public void setLongReadsRef(String longReadsRef) {
        this.longReadsRef = longReadsRef;
    }

    public LongReadsParams withLongReadsRef(String longReadsRef) {
        this.longReadsRef = longReadsRef;
        return this;
    }

    @JsonProperty("long_reads_type")
    public String getLongReadsType() {
        return longReadsType;
    }

    @JsonProperty("long_reads_type")
    public void setLongReadsType(String longReadsType) {
        this.longReadsType = longReadsType;
    }

    public LongReadsParams withLongReadsType(String longReadsType) {
        this.longReadsType = longReadsType;
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
        return ((((((("LongReadsParams"+" [longReadsRef=")+ longReadsRef)+", longReadsType=")+ longReadsType)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
