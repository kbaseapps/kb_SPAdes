package kb_SPAdes::kb_SPAdesClient;

use JSON::RPC::Client;
use POSIX;
use strict;
use Data::Dumper;
use URI;
use Bio::KBase::Exceptions;
my $get_time = sub { time, 0 };
eval {
    require Time::HiRes;
    $get_time = sub { Time::HiRes::gettimeofday() };
};

use Bio::KBase::AuthToken;

# Client version should match Impl version
# This is a Semantic Version number,
# http://semver.org
our $VERSION = "0.1.0";

=head1 NAME

kb_SPAdes::kb_SPAdesClient

=head1 DESCRIPTION


A KBase module: kb_SPAdes
A wrapper for the SPAdes assembler with hybrid features supported.
http://bioinf.spbau.ru/spades

Always runs in careful mode.
Runs 3 threads / CPU.
Maximum memory use is set to available memory - 1G.
Autodetection is used for the PHRED quality offset and k-mer sizes.
A coverage cutoff is not specified.


=cut

sub new
{
    my($class, $url, @args) = @_;
    

    my $self = {
	client => kb_SPAdes::kb_SPAdesClient::RpcClient->new,
	url => $url,
	headers => [],
    };

    chomp($self->{hostname} = `hostname`);
    $self->{hostname} ||= 'unknown-host';

    #
    # Set up for propagating KBRPC_TAG and KBRPC_METADATA environment variables through
    # to invoked services. If these values are not set, we create a new tag
    # and a metadata field with basic information about the invoking script.
    #
    if ($ENV{KBRPC_TAG})
    {
	$self->{kbrpc_tag} = $ENV{KBRPC_TAG};
    }
    else
    {
	my ($t, $us) = &$get_time();
	$us = sprintf("%06d", $us);
	my $ts = strftime("%Y-%m-%dT%H:%M:%S.${us}Z", gmtime $t);
	$self->{kbrpc_tag} = "C:$0:$self->{hostname}:$$:$ts";
    }
    push(@{$self->{headers}}, 'Kbrpc-Tag', $self->{kbrpc_tag});

    if ($ENV{KBRPC_METADATA})
    {
	$self->{kbrpc_metadata} = $ENV{KBRPC_METADATA};
	push(@{$self->{headers}}, 'Kbrpc-Metadata', $self->{kbrpc_metadata});
    }

    if ($ENV{KBRPC_ERROR_DEST})
    {
	$self->{kbrpc_error_dest} = $ENV{KBRPC_ERROR_DEST};
	push(@{$self->{headers}}, 'Kbrpc-Errordest', $self->{kbrpc_error_dest});
    }

    #
    # This module requires authentication.
    #
    # We create an auth token, passing through the arguments that we were (hopefully) given.

    {
	my %arg_hash2 = @args;
	if (exists $arg_hash2{"token"}) {
	    $self->{token} = $arg_hash2{"token"};
	} elsif (exists $arg_hash2{"user_id"}) {
	    my $token = Bio::KBase::AuthToken->new(@args);
	    if (!$token->error_message) {
	        $self->{token} = $token->token;
	    }
	}
	
	if (exists $self->{token})
	{
	    $self->{client}->{token} = $self->{token};
	}
    }

    my $ua = $self->{client}->ua;	 
    my $timeout = $ENV{CDMI_TIMEOUT} || (30 * 60);	 
    $ua->timeout($timeout);
    bless $self, $class;
    #    $self->_validate_version();
    return $self;
}




=head2 run_SPAdes

  $output = $obj->run_SPAdes($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a kb_SPAdes.SPAdesParams
$output is a kb_SPAdes.SPAdesOutput
SPAdesParams is a reference to a hash where the following keys are defined:
	workspace_name has a value which is a string
	output_contigset_name has a value which is a string
	read_libraries has a value which is a reference to a list where each element is a kb_SPAdes.paired_end_lib
	dna_source has a value which is a string
	min_contig_length has a value which is an int
	kmer_sizes has a value which is a reference to a list where each element is an int
	skip_error_correction has a value which is a kb_SPAdes.bool
paired_end_lib is a string
bool is an int
SPAdesOutput is a reference to a hash where the following keys are defined:
	report_name has a value which is a string
	report_ref has a value which is a string

</pre>

=end html

=begin text

$params is a kb_SPAdes.SPAdesParams
$output is a kb_SPAdes.SPAdesOutput
SPAdesParams is a reference to a hash where the following keys are defined:
	workspace_name has a value which is a string
	output_contigset_name has a value which is a string
	read_libraries has a value which is a reference to a list where each element is a kb_SPAdes.paired_end_lib
	dna_source has a value which is a string
	min_contig_length has a value which is an int
	kmer_sizes has a value which is a reference to a list where each element is an int
	skip_error_correction has a value which is a kb_SPAdes.bool
paired_end_lib is a string
bool is an int
SPAdesOutput is a reference to a hash where the following keys are defined:
	report_name has a value which is a string
	report_ref has a value which is a string


=end text

=item Description

Run SPAdes on paired end libraries

=back

=cut

 sub run_SPAdes
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function run_SPAdes (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to run_SPAdes:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'run_SPAdes');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "kb_SPAdes.run_SPAdes",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'run_SPAdes',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method run_SPAdes",
					    status_line => $self->{client}->status_line,
					    method_name => 'run_SPAdes',
				       );
    }
}
 


=head2 run_HybridSPAdes

  $output = $obj->run_HybridSPAdes($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a kb_SPAdes.HybridSPAdesParams
$output is a kb_SPAdes.SPAdesOutput
HybridSPAdesParams is a reference to a hash where the following keys are defined:
	workspace_name has a value which is a string
	output_contigset_name has a value which is a string
	reads_libraries has a value which is a reference to a list where each element is a kb_SPAdes.ReadsParams
	long_reads_libraries has a value which is a reference to a list where each element is a kb_SPAdes.LongReadsParams
	dna_source has a value which is a string
	pipeline_options has a value which is a reference to a list where each element is a string
	kmer_sizes has a value which is a reference to a list where each element is an int
	min_contig_length has a value which is an int
	create_report has a value which is a kb_SPAdes.bool
ReadsParams is a reference to a hash where the following keys are defined:
	lib_ref has a value which is a kb_SPAdes.obj_ref
	orientation has a value which is a string
	lib_type has a value which is a string
obj_ref is a string
LongReadsParams is a reference to a hash where the following keys are defined:
	long_reads_ref has a value which is a kb_SPAdes.obj_ref
	long_reads_type has a value which is a string
bool is an int
SPAdesOutput is a reference to a hash where the following keys are defined:
	report_name has a value which is a string
	report_ref has a value which is a string

</pre>

=end html

=begin text

$params is a kb_SPAdes.HybridSPAdesParams
$output is a kb_SPAdes.SPAdesOutput
HybridSPAdesParams is a reference to a hash where the following keys are defined:
	workspace_name has a value which is a string
	output_contigset_name has a value which is a string
	reads_libraries has a value which is a reference to a list where each element is a kb_SPAdes.ReadsParams
	long_reads_libraries has a value which is a reference to a list where each element is a kb_SPAdes.LongReadsParams
	dna_source has a value which is a string
	pipeline_options has a value which is a reference to a list where each element is a string
	kmer_sizes has a value which is a reference to a list where each element is an int
	min_contig_length has a value which is an int
	create_report has a value which is a kb_SPAdes.bool
ReadsParams is a reference to a hash where the following keys are defined:
	lib_ref has a value which is a kb_SPAdes.obj_ref
	orientation has a value which is a string
	lib_type has a value which is a string
obj_ref is a string
LongReadsParams is a reference to a hash where the following keys are defined:
	long_reads_ref has a value which is a kb_SPAdes.obj_ref
	long_reads_type has a value which is a string
bool is an int
SPAdesOutput is a reference to a hash where the following keys are defined:
	report_name has a value which is a string
	report_ref has a value which is a string


=end text

=item Description

Run HybridSPAdes on paired end libraries with PacBio CLR and Oxford Nanopore reads

=back

=cut

 sub run_HybridSPAdes
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function run_HybridSPAdes (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to run_HybridSPAdes:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'run_HybridSPAdes');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "kb_SPAdes.run_HybridSPAdes",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'run_HybridSPAdes',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method run_HybridSPAdes",
					    status_line => $self->{client}->status_line,
					    method_name => 'run_HybridSPAdes',
				       );
    }
}
 


=head2 run_metaSPAdes

  $output = $obj->run_metaSPAdes($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a kb_SPAdes.SPAdesParams
$output is a kb_SPAdes.SPAdesOutput
SPAdesParams is a reference to a hash where the following keys are defined:
	workspace_name has a value which is a string
	output_contigset_name has a value which is a string
	read_libraries has a value which is a reference to a list where each element is a kb_SPAdes.paired_end_lib
	dna_source has a value which is a string
	min_contig_length has a value which is an int
	kmer_sizes has a value which is a reference to a list where each element is an int
	skip_error_correction has a value which is a kb_SPAdes.bool
paired_end_lib is a string
bool is an int
SPAdesOutput is a reference to a hash where the following keys are defined:
	report_name has a value which is a string
	report_ref has a value which is a string

</pre>

=end html

=begin text

$params is a kb_SPAdes.SPAdesParams
$output is a kb_SPAdes.SPAdesOutput
SPAdesParams is a reference to a hash where the following keys are defined:
	workspace_name has a value which is a string
	output_contigset_name has a value which is a string
	read_libraries has a value which is a reference to a list where each element is a kb_SPAdes.paired_end_lib
	dna_source has a value which is a string
	min_contig_length has a value which is an int
	kmer_sizes has a value which is a reference to a list where each element is an int
	skip_error_correction has a value which is a kb_SPAdes.bool
paired_end_lib is a string
bool is an int
SPAdesOutput is a reference to a hash where the following keys are defined:
	report_name has a value which is a string
	report_ref has a value which is a string


=end text

=item Description

Run SPAdes on paired end libraries for metagenomes

=back

=cut

 sub run_metaSPAdes
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function run_metaSPAdes (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to run_metaSPAdes:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'run_metaSPAdes');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "kb_SPAdes.run_metaSPAdes",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'run_metaSPAdes',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method run_metaSPAdes",
					    status_line => $self->{client}->status_line,
					    method_name => 'run_metaSPAdes',
				       );
    }
}
 
  
sub status
{
    my($self, @args) = @_;
    if ((my $n = @args) != 0) {
        Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
                                   "Invalid argument count for function status (received $n, expecting 0)");
    }
    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
        method => "kb_SPAdes.status",
        params => \@args,
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
                           code => $result->content->{error}->{code},
                           method_name => 'status',
                           data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
                          );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method status",
                        status_line => $self->{client}->status_line,
                        method_name => 'status',
                       );
    }
}
   

sub version {
    my ($self) = @_;
    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
        method => "kb_SPAdes.version",
        params => [],
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(
                error => $result->error_message,
                code => $result->content->{code},
                method_name => 'run_metaSPAdes',
            );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(
            error => "Error invoking method run_metaSPAdes",
            status_line => $self->{client}->status_line,
            method_name => 'run_metaSPAdes',
        );
    }
}

sub _validate_version {
    my ($self) = @_;
    my $svr_version = $self->version();
    my $client_version = $VERSION;
    my ($cMajor, $cMinor) = split(/\./, $client_version);
    my ($sMajor, $sMinor) = split(/\./, $svr_version);
    if ($sMajor != $cMajor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Major version numbers differ.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor < $cMinor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Client minor version greater than Server minor version.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor > $cMinor) {
        warn "New client version available for kb_SPAdes::kb_SPAdesClient\n";
    }
    if ($sMajor == 0) {
        warn "kb_SPAdes::kb_SPAdesClient version is $svr_version. API subject to change.\n";
    }
}

=head1 TYPES



=head2 bool

=over 4



=item Description

A boolean. 0 = false, anything else = true.


=item Definition

=begin html

<pre>
an int
</pre>

=end html

=begin text

an int

=end text

=back



=head2 paired_end_lib

=over 4



=item Description

The workspace object name of a PairedEndLibrary file, whether of the
KBaseAssembly or KBaseFile type.


=item Definition

=begin html

<pre>
a string
</pre>

=end html

=begin text

a string

=end text

=back



=head2 SPAdesParams

=over 4



=item Description

Input parameters for running SPAdes.
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


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
workspace_name has a value which is a string
output_contigset_name has a value which is a string
read_libraries has a value which is a reference to a list where each element is a kb_SPAdes.paired_end_lib
dna_source has a value which is a string
min_contig_length has a value which is an int
kmer_sizes has a value which is a reference to a list where each element is an int
skip_error_correction has a value which is a kb_SPAdes.bool

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
workspace_name has a value which is a string
output_contigset_name has a value which is a string
read_libraries has a value which is a reference to a list where each element is a kb_SPAdes.paired_end_lib
dna_source has a value which is a string
min_contig_length has a value which is an int
kmer_sizes has a value which is a reference to a list where each element is an int
skip_error_correction has a value which is a kb_SPAdes.bool


=end text

=back



=head2 obj_ref

=over 4



=item Description

An X/Y/Z style KBase object reference


=item Definition

=begin html

<pre>
a string
</pre>

=end html

=begin text

a string

=end text

=back



=head2 ReadsParams

=over 4



=item Description

parameter groups--define attributes for specifying inputs with YAML data set file (advanced)
The following attributes are available:

     - orientation ("fr", "rf", "ff")
     - type ("paired-end", "mate-pairs", "hq-mate-pairs", "single", "pacbio", "nanopore", "sanger", "trusted-contigs", "untrusted-contigs")
     - interlaced reads (comma-separated list of files with interlaced reads)
     - left reads (comma-separated list of files with left reads)
     - right reads (comma-separated list of files with right reads)
     - single reads (comma-separated list of files with single reads or unpaired reads from paired library)
     - merged reads (comma-separated list of files with merged reads)


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
lib_ref has a value which is a kb_SPAdes.obj_ref
orientation has a value which is a string
lib_type has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
lib_ref has a value which is a kb_SPAdes.obj_ref
orientation has a value which is a string
lib_type has a value which is a string


=end text

=back



=head2 LongReadsParams

=over 4



=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
long_reads_ref has a value which is a kb_SPAdes.obj_ref
long_reads_type has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
long_reads_ref has a value which is a kb_SPAdes.obj_ref
long_reads_type has a value which is a string


=end text

=back



=head2 HybridSPAdesParams

=over 4



=item Description

------To run HybridSPAdes 3.13.0 you need at least one library of the following types:------
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


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
workspace_name has a value which is a string
output_contigset_name has a value which is a string
reads_libraries has a value which is a reference to a list where each element is a kb_SPAdes.ReadsParams
long_reads_libraries has a value which is a reference to a list where each element is a kb_SPAdes.LongReadsParams
dna_source has a value which is a string
pipeline_options has a value which is a reference to a list where each element is a string
kmer_sizes has a value which is a reference to a list where each element is an int
min_contig_length has a value which is an int
create_report has a value which is a kb_SPAdes.bool

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
workspace_name has a value which is a string
output_contigset_name has a value which is a string
reads_libraries has a value which is a reference to a list where each element is a kb_SPAdes.ReadsParams
long_reads_libraries has a value which is a reference to a list where each element is a kb_SPAdes.LongReadsParams
dna_source has a value which is a string
pipeline_options has a value which is a reference to a list where each element is a string
kmer_sizes has a value which is a reference to a list where each element is an int
min_contig_length has a value which is an int
create_report has a value which is a kb_SPAdes.bool


=end text

=back



=head2 SPAdesOutput

=over 4



=item Description

Output parameters for SPAdes run.

    report_name - the name of the KBaseReport.Report workspace object.
    report_ref - the workspace reference of the report.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
report_name has a value which is a string
report_ref has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
report_name has a value which is a string
report_ref has a value which is a string


=end text

=back



=cut

package kb_SPAdes::kb_SPAdesClient::RpcClient;
use base 'JSON::RPC::Client';
use POSIX;
use strict;

#
# Override JSON::RPC::Client::call because it doesn't handle error returns properly.
#

sub call {
    my ($self, $uri, $headers, $obj) = @_;
    my $result;


    {
	if ($uri =~ /\?/) {
	    $result = $self->_get($uri);
	}
	else {
	    Carp::croak "not hashref." unless (ref $obj eq 'HASH');
	    $result = $self->_post($uri, $headers, $obj);
	}

    }

    my $service = $obj->{method} =~ /^system\./ if ( $obj );

    $self->status_line($result->status_line);

    if ($result->is_success) {

        return unless($result->content); # notification?

        if ($service) {
            return JSON::RPC::ServiceObject->new($result, $self->json);
        }

        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    elsif ($result->content_type eq 'application/json')
    {
        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    else {
        return;
    }
}


sub _post {
    my ($self, $uri, $headers, $obj) = @_;
    my $json = $self->json;

    $obj->{version} ||= $self->{version} || '1.1';

    if ($obj->{version} eq '1.0') {
        delete $obj->{version};
        if (exists $obj->{id}) {
            $self->id($obj->{id}) if ($obj->{id}); # if undef, it is notification.
        }
        else {
            $obj->{id} = $self->id || ($self->id('JSON::RPC::Client'));
        }
    }
    else {
        # $obj->{id} = $self->id if (defined $self->id);
	# Assign a random number to the id if one hasn't been set
	$obj->{id} = (defined $self->id) ? $self->id : substr(rand(),2);
    }

    my $content = $json->encode($obj);

    $self->ua->post(
        $uri,
        Content_Type   => $self->{content_type},
        Content        => $content,
        Accept         => 'application/json',
	@$headers,
	($self->{token} ? (Authorization => $self->{token}) : ()),
    );
}



1;
