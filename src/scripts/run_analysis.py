from src.app.models import MainConfig
from src.app.analyser.analyser import TradingAnalyser


def start_analysis(config:MainConfig):
    analyser = TradingAnalyser(config)
    analyser.start_analysis()