"""
This Python retrieves Non-sequence metadata
Input: gene id
Output: print stdout
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id=28
"""
from Bio import Entrez

class GeneRetrieve():
    def __init__(self, gene_id, api_key=None):
        Entrez.email = "codeathon@example.com"
        if api_key:
            Entrez.api_key = api_key
        self.handle_summary = Entrez.esummary(db="gene", id=gene_id, rettype="xml")
        self.handle_full = Entrez.efetch(db="gene", id=gene_id, rettype="xml")
        self.handle_gene2pubmed = Entrez.elink(dbfrom="gene", db="pubmed", id=gene_id, rettype="xml")

    def record(self):
        record_summary = Entrez.read(self.handle_summary)
        record_full = Entrez.read(self.handle_full)
        record_gene2pubmed = Entrez.read(self.handle_gene2pubmed)
        return record_summary['DocumentSummarySet']['DocumentSummary'][0], record_full[0], record_gene2pubmed[0]


class GeneData():
    def __init__(self, gene_id, api_key):
        gene_record = GeneRetrieve(gene_id, api_key)
        self.doc_summary, self.doc_full, self.doc_pubmed = gene_record.record()

    def pretty_print_field(self, dom_element):
        if dom_element.in_esummary == "Gene2Pubmed":
            return dom_element.pretty_print(self.doc_pubmed)
        if dom_element.in_esummary:
            return dom_element.pretty_print(self.doc_summary)
        return dom_element.pretty_print(self.doc_full)


class DomElement():
    def __init__(self, tag_name, attribute_name=None,  in_esummary=True):
        self.tag = tag_name
        self.attribute_name = attribute_name
        self.in_esummary = in_esummary

    def pretty_print(self, doc):
        if self.in_esummary == "Gene2Pubmed":
            pubmed_ids = []
            for link in doc['LinkSetDb'][0]['Link']:
                pubmed_ids.append(link['Id'])
            return ', '.join(pubmed_ids)
        if self.tag == "GeneExpression":
            tissue = ""
            for comm in doc['Entrezgene_comments']:
                if comm.get('Gene-commentary_heading') == 'Representative Expression':
                    for gene_comm in comm['Gene-commentary_comment']:
                        if gene_comm['Gene-commentary_label'] == 'Tissue List':
                            tissue = gene_comm['Gene-commentary_text']
            return tissue
        if self.attribute_name:
            return getattr(doc[self.tag], 'attributes')[self.attribute_name]
        else:
            return doc[self.tag]


class GeneMetaReport():

    def __init__(self, gene_list, api_key):
        self.genes = gene_list
        self.api_key = api_key
        self.field_list = [('Summary', DomElement('Summary', None, True)),
                  ('Symbol', DomElement('Name', None, True)),
                  ('Aliases', DomElement('OtherAliases', None, True)),
                  ('Description', DomElement('Description', None, True)),
                  ('Type', DomElement('Entrezgene_type', 'value', False)),
                  ('Publications', DomElement('', None, "Gene2Pubmed")),
                  ('Expression', DomElement('GeneExpression', None, False)),
                 ]

    def write_report(self, tsv_output):
        fields = []
        for field in self.field_list:
            fields.append(field[0])
        tsv_output.write('Id\t' + '\t'.join(fields) + "\r\n")
        for gene_id in self.genes:
            data = GeneData(gene_id, self.api_key)
            field_val = []
            for _, val in self.field_list:
                field_val.append(data.pretty_print_field(val))
            tsv_output.write(str(gene_id) + '\t' + '\t'.join(field_val) + "\r\n")
