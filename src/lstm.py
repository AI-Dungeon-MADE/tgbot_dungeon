from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

tokens = [' ', 'а', 'б', 'в', 'г', 'д', 'е', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о',
          'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я', 'ё']

# dict <index>:<char>
idx_to_token = {idx: tok for tok, idx in zip(tokens, range(len(tokens)))}
token_to_idx = {tok: idx for tok, idx in zip(tokens, range(len(tokens)))}
num_tokens = len(tokens)


class CharLSTM(nn.Module):
    def __init__(self, num_tokens=num_tokens, emb_size=num_tokens,
                 num_units=64, num_layers=2, dropout=0.01):
        super(self.__class__, self).__init__()

        self.num_units = num_units
        self.num_layers = num_layers
        self.emb = nn.Embedding(num_tokens, emb_size)
        self.rnn = nn.LSTM(emb_size, num_units, batch_first=True,
                           num_layers=num_layers, dropout=dropout)
        self.hid_to_logits = nn.Linear(num_units, num_tokens)

    def forward(self, x, hid_state=None):
        if hid_state is None:
            h_seq, _ = self.rnn(self.emb(x))
            next_logits = self.hid_to_logits(h_seq)
            next_logp = F.log_softmax(next_logits, dim=-1)
            return next_logp
        else:
            h_seq, hid_state = self.rnn(self.emb(x), hid_state)
            next_logits = self.hid_to_logits(h_seq)
            next_logp = F.log_softmax(next_logits, dim=-1)
            return next_logp, hid_state

    def initial_state(self, batch_size):
        """Return RNN state before it processes the first input (h0)."""
        return torch.zeros(self.num_layers, batch_size, self.num_units), \
               torch.zeros(self.num_layers, batch_size, self.num_units)

    def generate_text(self, seed_phrase: str = ' ', hid_state: Optional[torch.Tensor] = None, max_length=100,
                      temperature=1.0) -> tuple[str, tuple[torch.Tensor, ...]]:
        # model.to('cpu')
        x_sequence = [token_to_idx[token] for token in seed_phrase.lower() if token in tokens]
        x_sequence = torch.tensor([x_sequence], dtype=torch.int64)
        if hid_state is None:
            hid_state = self.initial_state(batch_size=1)
        # start generating
        for i in range(max_length - len(seed_phrase)):
            logp_next, hid_state = self.forward(x_sequence[..., -1:], hid_state)
            p_next = F.softmax(logp_next / temperature, dim=-1).data.numpy().squeeze()
            # sample next token and push it back into x_sequence
            next_ix = np.random.choice(num_tokens, p=p_next)
            next_ix = torch.tensor([[next_ix]], dtype=torch.int64)
            x_sequence = torch.cat([x_sequence, next_ix], dim=-1)

        generated_text = ''.join([tokens[ix] for ix in x_sequence.data.numpy()[0]])
        return generated_text, hid_state
