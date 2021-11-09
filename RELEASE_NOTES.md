### Version 1.3.2
__Changes__
- changed THREADS_PER_CORE to 1
- changed MAX_THREADS to 32 (for bigmem worker pool)
- changed MAX_THREADS_META to 64 (for extreme worker pool)

### Version 1.3.1
__Changes__
- updated SPAdes to 3.15.3
- dropped kb_SPAdesImpl.py MIN_MEMORY_GB from 5 to 4 to fit in Github Actions test node
- changed default output object name to <method_name>.Assembly

### Version 1.3.0
__Changes__
- updated SPAdes to 3.15.2
- added github actions tests
- made unit test data upload via ReadsUtil.upload_reads()
- fixed broken unit tests
- completed port from python 2 to 3

### Version 1.2.5
__Changes__
- removed HTML from input params to hybridSPAdes

### Version 1.2.4
__Changes__
- matched the pacbio* strings from within the main code to the values in the ui dropdown

### Version 1.2.3
__Changes__
- update docs

### Version 1.2.0
__Changes__
- updated to 3.13 and added hybrid spades feature

### Version 1.1.4
__Changes__
- added citations in PLOS format

### Version 1.1.3
__Changes__
- updated to SPAdes 3.12.0

### Version 1.1.2
__Changes__
- added advanced parameters to set list of Kmer sizes and option to skip read error correction

### Version 1.1.1
__Changes__
- changed contact from email to url

### Version 1.1.0
__Changes__
- updated version of SPAdes to 3.11.1

### Version 1.0.0
__Changes__
- updated metaSPAdes() min_contig_length parameter to required and changed default values to min:300bp default: 2Kbp

### Version 0.0.9
__Changes__
- Added min_contig_length parameter for metaSPAdes
- Limited MetaSPAdes narrative UI to accept only one reads input
- Limit SPAdes and MetaSPAdes memory usage to 100GB and 500GB respectively.
- Removed requirement for 'single_genome' flag not set for metagenomic assembly
- Added travis CI
