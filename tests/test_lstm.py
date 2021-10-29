import torch

from src.lstm import CharLSTM
from made_ai_dungeon import StoryManager


def test_char_lstm() -> None:
    model = CharLSTM(num_layers=2, num_units=196, dropout=0.05)
    model.load_state_dict(torch.load('./models/Char_LSTM_Samurai.pth'))
    story_manager = StoryManager(model)
    generated_story = story_manager.generate_story("chat_id2", "Начальная фраза")
    assert isinstance(generated_story, str)
    assert story_manager.story_context_cache.get("chat_id2") is not None
    generated_story = story_manager.generate_story("chat_id2", "новые слова")
    assert isinstance(generated_story, str)
