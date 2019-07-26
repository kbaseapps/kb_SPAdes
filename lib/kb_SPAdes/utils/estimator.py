def estimate_metaSPAdes_reqs(params, ws):
    """
    Generates an estimate of how much computational power is needed to run metaSPAdes.
    params: dict with keys (only relevant ones given):
        * workspace_name - name of workspace
        * output_contigset_name
        * read_libaries - list of names of Paired End library objects
        * dna_source - string - source of dna?
        * min_contig_length - int - min contigs to keep in assembly
        * kmer_sizes - int - length of kmers to use in assembly
        * skip_error_correction - int - if 1, skips error correction step
    return: dict with keys:
        * cpus - int value > 0 - # of cpu cores required
        * memory - int value > 0 - amount of memory needed in MB
        * walltime - int value > 0 - seconds of time estimated to run
    """
    if not params.get("workspace_name"):
        raise ValueError("workspace_name is required to estimate metaSPAdes requirements!")
    if len(params.get("read_libraries", [])) == 0:
        raise ValueError("At least one read library is required to estimate metaSPAdes requirements!")

    ws_name = params.get("workspace_name")
    reads_refs = []
    for lib_name in params["read_libraries"]:
        reads_refs.append({"ref": lib_name if "/" in lib_name else ws_name + "/" + lib_name})
    reads_infos = ws.get_object_info3({
        "objects": reads_refs,
        "includeMetadata": 1
    })

    missing_meta = 0
    kmer_list = []
    kmer_len = 31
    for reads in reads_infos['infos']:
        meta = reads[10]
        if 'read_count' in meta and 'read_length_mean' in meta:
            total_reads = int(meta['read_count'])
            read_len = float(meta['read_length_mean'])
            # total number of kmers per read -- upper bound (# unique will be <= the below)
            kmer_list.append(total_reads * max(0, read_len - kmer_len + 1))
        else:
            missing_meta += 1
    print(reads_infos)
    print(kmer_list)
    print(missing_meta)
    avg_kmer_count = sum(kmer_list)/len(kmer_list)
    total_kmers = sum(kmer_list) + (avg_kmer_count * missing_meta)

    # now we have an approximation of how many kmers there are. we can use
    # that to guesstimate how much memory we need

    predicted_mem = (total_kmers * 2.962e-08 + 16.3) * 1.1 * 1024

    est = {
        "cpus": 16,
        "memory": max(int(predicted_mem), 4096),
        "walltime": max(total_kmers/100000, 300)
    }

    return est
