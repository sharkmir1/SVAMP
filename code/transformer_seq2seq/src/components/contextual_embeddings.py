import ipdb
import torch.nn as nn
import torch
from transformers import BertModel, BertTokenizer, RobertaModel, RobertaTokenizer
import pdb


class RobertaEncoder(nn.Module):
    def __init__(self, roberta_model='roberta-base', device='cuda:0 ', freeze_roberta=False):
        super(RobertaEncoder, self).__init__()
        self.roberta_layer = RobertaModel.from_pretrained(roberta_model)
        self.roberta_tokenizer = RobertaTokenizer.from_pretrained(roberta_model)
        self.device = device

        if freeze_roberta:
            for p in self.roberta_layer.parameters():
                p.requires_grad = False

    def robertify_input(self, sentences):
        '''
        Preprocess the input sentences using roberta tokenizer and converts them to a torch tensor containing token ids

        Args:
            sentences (list): source sentences
        Returns:
            token_ids (tensor): tokenized sentences | size: [BS x S]
            attn_masks (tensor): masks padded indices | size: [BS x S]
            input_lengths (list): lengths of sentences | size: [BS]
        '''

        # Tokenize the input sentences for feeding into RoBERTa
        all_tokens = [['<s>'] + self.roberta_tokenizer.tokenize(sentence) + ['</s>'] for sentence in sentences]

        # Pad all the sentences to a maximum length
        input_lengths = [len(tokens) for tokens in all_tokens]
        max_length = max(input_lengths)
        padded_tokens = [tokens + ['<pad>' for _ in range(max_length - len(tokens))] for tokens in all_tokens]

        # Convert tokens to token ids
        token_ids = torch.tensor([self.roberta_tokenizer.convert_tokens_to_ids(tokens) for tokens in padded_tokens]).to(
            self.device)

        # Obtain attention masks
        pad_token = self.roberta_tokenizer.convert_tokens_to_ids('<pad>')
        attn_masks = (token_ids != pad_token).long()

        return token_ids, attn_masks, input_lengths

    def forward(self, sentences):
        '''
        Feed the batch of sentences to a RoBERTa encoder to obtain contextualized representations of each token

        Args:
            sentences (list): source sentences
        Returns:
            cont_reps (tensor): RoBERTa Embeddings | size: [BS x S x d_model]
            token_ids (tensor): tokenized sentences | size: [BS x S]
        '''

        # Preprocess sentences
        token_ids, attn_masks, input_lengths = self.robertify_input(sentences)

        # Feed through RoBERTa
        cont_reps = self.roberta_layer(token_ids, attention_mask=attn_masks)['last_hidden_state']

        return cont_reps, token_ids
