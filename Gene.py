import utils
import changes
import collections
from Bio import Seq

class Gene:
    def __init__(self, gene_name, scaf_name, strand):
        self.name = gene_name
        self.scaf = scaf_name
        self.cds = []
        self.introns = []
        self.five_utrs = []
        self.three_utrs = []
        self.start = -1
        self.end = -1
        self.sequence = {}
        self.strand = strand
        self.species = gene_name[0:4]
        self.alts = {}
        self.refs = {}
        self.syn_count = -1 #PS
        self.nsyn_count = -1 #PR
        self.potent_syn = -1 #Tsil
        self.potent_nsyn = -1 #Trepl
        self.average_n = -1 #npop
        self.intron_dic = {}
        self.utr3_dic = {}
        self.utr5_dic = {}
        self.flank_dic = {}
        self.flank_subs = -1 
        self.intron_subs = -1
        self.utr3_subs = -1
        self.utr5_subs =-1
        self.called_counts = {}
        self.flank_start = -1
        self.flank_end = -1
        self.average_n = 0
        self.flank_seq = ""
        self.intron_seq = ""
        
    def add_cds(self, cds_list):
        self.cds = cds_list
        self.get_introns()

    def add_utrs(self, utr_list, prime_end):
        if prime_end == "three":
            self.three_utrs = utr_list
        elif prime_end == "five":
            self.five_utrs = utr_list

    def set_start(self, start_coord):
        self.start = start_coord
    
    def set_end(self, end_coord):
        self.end = end_coord

    def set_sequence(self, scaf_seq, flank_size):
        seq_dic = collections.OrderedDict()
        cur_start = self.start - flank_size
        cur_end = self.end + flank_size
        if cur_start < 0:
            cur_start = 0
        if cur_end > len(scaf_seq):
            cur_end = len(scaf_seq)
        index = cur_start
        while index <= cur_end:
            seq_dic[index] = scaf_seq[index-1]
            index += 1
        self.sequence = seq_dic
        self.flank_start = cur_start
        self.flank_end = cur_end

    def get_introns(self):
        intron_list = []
        for x in range(len(self.cds)-1):
            cur_intron = (self.cds[x][1], self.cds[x+1][0])
            intron_list.append(cur_intron)
        self.introns = intron_list

    def get_intron_sequence(self):
        intron_dic = collections.OrderedDict()
        for site, nuc in self.sequence.items():
            for intron in self.introns:
                if site >= intron[0] and site <= intron[1]:
                    intron_dic[site] = nuc
        self.intron_dic = intron_dic
        self.intron_seq = "".join(intron_dic.values())

    def get_utr_sequence(self):
        utr_dic = collections.OrderedDict()
        for site, nuc in self.sequence.items():
            for utr in self.three_utrs:
                if site >= utr[0] and site <= utr[1]:
                    utr_dic[site] = nuc
        self.utr3_dic = utr_dic
        utr_dic = collections.OrderedDict()
        for site, nuc in self.sequence.items():
            for utr in self.five_utrs:
                if site >= utr[0] and site <= utr[1]:
                    utr_dic[site] = nuc
        self.utr5_dic = utr_dic

    def get_flank_sequence(self, flank_size):
        flank_dic = collections.OrderedDict()
        for site, nuc in self.sequence.items():
            if self.strand == 1:
                if site < self.start:
                    flank_dic[site] = nuc
            elif self.strand == -1:
                if site > self.end:
                    flank_dic[site] = nuc
        self.flank_dic = flank_dic
        self.flank_seq = "".join(flank_dic.values())
    
    def get_cds_sequence(self, seq_dic):
        cds_dic = collections.OrderedDict()
        for site, nuc in self.sequence.items():
            for exon in self.cds:
                if site >= exon[0] and site <= exon[1]:
                    cds_dic[site] = nuc
        recon_seq = "".join(cds_dic.values())
        if self.strand == -1:
            recon_seq = str(Seq.Seq(recon_seq).reverse_complement())
        if recon_seq != seq_dic[self.name]:
            raise ImportError("Failed to reconstruct CDS for %s" % self.name)
        self.cds = cds_dic

    def noncoding_subs(self):
        flank_subs = 0
        intron_subs = 0
        utr3_subs = 0
        utr5_subs = 0
        for index in self.alts.keys():
            if index in self.flank_dic.keys():
                for x in range(len(self.alts[index])):
                    if x > len(self.refs[index]) - 1:
                        break
                    if str(self.alts[index])[x] != str(self.refs[index])[x]:
                        flank_subs += 1
            if index in self.intron_dic.keys():
                for x in range(len(self.alts[index])):
                    if x > len(self.refs[index]) - 1:
                        break
                    if str(self.alts[index])[x] != str(self.refs[index])[x]:
                        intron_subs += 1
            if index in self.utr3_dic.keys():                
                for x in range(len(self.alts[index])):
                    if x > len(self.refs[index]) - 1:
                        break
                    if str(self.alts[index])[x] != str(self.refs[index])[x]:
                        utr3_subs += 1
            if index in self.utr5_dic.keys():                
                for x in range(len(self.alts[index])):
                    if x > len(self.refs[index]) - 1:
                        break
                    if str(self.alts[index])[x] != str(self.refs[index])[x]:
                        utr5_subs += 1
        self.flank_subs = flank_subs
        self.intron_subs = intron_subs
        self.utr3_subs = utr3_subs
        self.utr5_subs = utr5_subs
                

    def syn_and_nsyn(self):
        syn_count = 0
        nsyn_count = 0
#        if self.name != "LMAL_05156":
#            return
        print self.name
        for index in self.alts.keys():
            old_codon = ""
            new_codon = []
            if index in self.cds.keys():
                if len(self.alts[index]) != len(self.refs[index]):
                    nsyn_count += 1
                    continue
                variant_len = len(self.alts[index])
                if self.strand == 1:
                    cds_index = self.cds.keys().index(index)

                    if cds_index + variant_len >= len(self.cds):
                        variant_len = len(self.cds) - cds_index - 1 #not sure about - 1
                        self.alts[index] = str(self.alts[index])[0:variant_len]

#                    print self.alts[index]
#                    print index
#                    print cds_index
#                    codon_start = index - (cds_index % 3)
#                    codon_start = cds_index + (cds_index % 3) + ((variant_len / 3) * 3)
                    codon_start = cds_index - (cds_index % 3) #+ ((variant_len / 3) * 3)
                    leftover_len = variant_len - (3 - cds_index % 3)
                    additional_len = 3 * (leftover_len / 3)
                    if leftover_len % 3 > 0:
                        additional_len += 3
#                    for x in range(3 + ((variant_len / 3) * 3) + variant_len % 3 * 3):
#                    print codon_start
#                    print leftover_len
#                    print additional_len
#                    print variant_len
                    for x in range(3+additional_len):
                        new_index = codon_start + x
                        new_index = self.cds.keys()[new_index]
#                        old_codon += self.cds[codon_start + x]
                        old_codon += self.cds[new_index]
#                        new_codon.append(self.cds[codon_start + x])
                        new_codon.append(self.cds[new_index])
#                        print new_codon
#                        print old_codon
#                    new_codon[cds_index % 3] = str(self.alts[index])
                    for x in range(variant_len):
                        new_codon[cds_index % 3 + x] = str(self.alts[index])[x]
                    old_codon = Seq.Seq(old_codon)
                    new_codon = Seq.Seq("".join(new_codon))
#                    print old_codon
#                    print new_codon

                elif self.strand == -1:
                    cds_index = len(self.cds.keys()) - 1 - self.cds.keys().index(index)
#                    print cds_index
                    if cds_index - variant_len < 0:
                        variant_len = cds_index
                        self.alts[index] = str(self.alts[index])[0:variant_len]
#                    codon_start = index + (cds_index % 3) + ((variant_len / 3) * 3)
                    codon_start = len(self.cds.keys()) - 1 - cds_index + (cds_index % 3) + ((variant_len / 3) * 3)
#                    print codon_start
#                    codon_start = self.cds.keys().index(index + (cds_index % 3) + ((variant_len / 3) * 3))

                    leftover_len = variant_len - (3 - cds_index % 3)
                    additional_len = 3 * (leftover_len / 3)
                    if leftover_len % 3 > 0:
                        additional_len += 3

#                    for x in range(3 + ((variant_len / 3) * 3)):
#                    print leftover_len
#                    print additional_len
#                    print variant_len
#                    while codon_start + additional_len >= len(self.cds):
#                        additional_len -= 1
#                        variant_len -= 1
#                    if codon_start + additional_len > len(self.cds):
                        
                    for x in range(3 + additional_len):
                        new_index = codon_start - x
                            
#                        print new_index
                        new_index = self.cds.keys()[new_index]
#                        if codon_start - x not in self.cds.keys():
#                            new_index = self.reverse_adjacent_site(codon_start - x, codon_start )
#                        old_codon += self.cds[codon_start - x]
                        old_codon += self.cds[new_index]
#                        new_codon.append(self.cds[codon_start - x])
                        new_codon.append(self.cds[new_index])
#                        print old_codon
#                        print new_codon
#                    new_codon[cds_index % 3] = str(self.alts[index])
#                    print new_codon
                    for x in range(variant_len):
                        new_codon[cds_index % 3 + x] = str(self.alts[index])[variant_len - x - 1]
#                    print new_codon
                    old_codon = Seq.Seq(old_codon).complement()
                    new_codon = Seq.Seq("".join(new_codon)).complement()
#                    print old_codon
#                    print new_codon
                old_aa = str(old_codon.translate())
                new_aa = str(new_codon.translate())
                temp_nsyn = 0
                for aa in range(len(new_aa)):
                    if old_aa[aa] != new_aa[aa]:
                        nsyn_count += 1
                        temp_nsyn += 1
                temp_syn = 0
                for nuc in range(len(str(new_codon))):
                    if str(old_codon)[nuc] != str(new_codon)[nuc]:
                        syn_count += 1
                        temp_syn 
                syn_count = syn_count - temp_nsyn
#                else:
                    #This must be a frameshift mutation which is a disaster and is, therefore, probably not a real variant so don't count it
#                    continue
        self.syn_count = syn_count
        self.nsyn_count = nsyn_count
    
#    def reverse_adjacent_site(self, missing_site):
#        new_site = -1
#        for site in self.cds.keys():
#            if site > missing_site:
#                continue
#            if site < missing_site:
#                new_site = site
#        return new_site

    def average_sample_size(self, target_dic):
        return self.average_n
        size_sum = 0
        num_sites = 0
        for site in target_dic.keys():
            num_sites += 1
            size_sum += self.called_counts[site]
        #trying to make it faster
#        for site, size in self.called_counts.items():
#            if site in target_dic.keys():
#                num_sites += 1
#                size_sum += size
        if num_sites == 0:
            return 0
        return size_sum / num_sites

    def get_genotypes(self, vcf_reader, flank_size):
        scaf_len = vcf_reader.contigs[self.scaf][1]
        called_site_count = 0
        alt_dic = {}
        called_count = {}
        ref_dic = {}
        try:
            reader = vcf_reader.fetch(self.scaf, self.flank_start, self.flank_end)
#            reader = vcf_reader.fetch("LMAL_scaf_1047", self.flank_start - 1, self.flank_end)
            print "made reader"
        except ValueError:
            print "can't get that bit of vcf"
            self.alts = {}
            self.refs = {}
            self.called_counts = {}
            self.potential_sites()
            return
            
        for rec in reader: #vcf_reader.fetch(self.scaf, self.flank_start - 1, self.flank_end):
            if rec.num_called < 4:
                continue
            elif rec.num_called == rec.num_hom_ref:
                called_count[rec.POS] = rec.num_called
                continue
            elif rec.num_called == rec.num_het or rec.num_called == rec.num_hom_alt:
                self.sequence[rec.POS] = "N"
                continue
            half_missing = 0
            for s in rec.samples:
                if str(s.data.GT) in ["./1", "./0", "1/.", "0/."]:
                    half_missing += 1
            if (rec.num_called - half_missing) == rec.num_hom_alt or (rec.num_called - half_missing) == rec.num_het:
                continue
            else:
                alt_dic[rec.POS] = rec.ALT[0]
                ref_dic[rec.POS] = rec.REF
                called_count[rec.POS] = rec.num_called
        #lower memory use? faster?
#        self.called_counts = called_count
        self.average_n = sum(called_count.values()) / len(called_count.values())
        self.alts = alt_dic
        self.refs = ref_dic
        self.syn_and_nsyn()
        self.potential_sites()
        self.noncoding_subs()
        #reduce memory usage?
        self.refs = {}
        self.alts = {}
        self.cds = {}
        self.flank_dic = {}
        self.intron_dic = {}

    def potential_sites(self):
        potent_dic = changes.potent_dic()
        cur_cds = "".join(self.cds.values())
        if self.strand == -1:
            cur_cds = str(Seq.Seq(cur_cds).reverse_complement())
        x = 0
        syn_sites = 0
        nsyn_sites = 0
        while x < len(cur_cds):
            ambig_codon = False
            codon = cur_cds[x:x+3].upper()
            for ambig in ["N", "M", "R", "W", "S", "Y", "K", "V", "H", "D", "B"]:
                if ambig in codon:
                    ambig_codon = True
            if ambig_codon:
                x = x + 3
                ambig_codon = False
                continue
            nsyn_sites += potent_dic["N"][codon]
            syn_sites += potent_dic["S"][codon]
            x = x + 3
        self.potent_syn = syn_sites
        self.potent_nsyn = nsyn_sites
            
    def add_site_to_samples(self, vcf_rec, sample_dic, index):
        if vcf_rec.num_called >= 3:
            if vcf_rec.num_called == vcf_rec.num_het or vcf_rec.num_called == vcf_rec.num_hom_alt:
                for s in vcf_rec.samples:
                    sample_dic[s.sample].add_site(index, "N", "N", s.data.GT)
            else:
                for s in vcf_rec.samples:
                    sample_dic[s.sample].add_site(index, vcf_rec.REF, vcf_rec.ALT, s.data.GT)
            

