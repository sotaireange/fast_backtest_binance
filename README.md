# VectorBT Backtesting Framework

A high-performance framework for backtesting crypto futures trading strategies using `vectorbt` and `numba`. The platform enables rapid testing of complex parameter combinations across a large number of assets.

## Core Features

-   **Fast Backtesting**: Utilizes `numba` to compile Python code into machine code and `vectorbt` for vectorized computations.
-   **Flexible Strategy Design**: Create and register your own trading strategies with any set of parameters.
-   **Combinatorial Analysis**: Automatically generate and test thousands of parameter combinations to find optimal settings.
-   **Multiprocessing**: Distributes the workload across multiple CPU cores to accelerate bulk computations.
-   **Automatic Data Download**: Integrated with the Binance API to download historical data.
-   **Results Analysis**: Saves and aggregates results for subsequent analysis.

---  

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Numba](https://img.shields.io/badge/Numba-00A3E0?style=for-the-badge&logo=python&logoColor=white)
![VectorBT](https://img.shields.io/badge/VectorBT-1A1A1A?style=for-the-badge)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)  
![Rich](https://img.shields.io/badge/Rich-9C27B0?style=for-the-badge&logo=python&logoColor=white)


---  

## Getting Started

### Requirements

-   Python 3.10+
-   vectorbt 0.28

### Installation

1.  Clone the repository:
    ```bash  
    git clone <your-repo-link>  
    cd <repo-name>    ```  
2.  Install dependencies:
    ```bash  
    pip install -r requirements.txt  
    ```  
3.  Configure the main `config/config.yaml` file.

---  

## How to Write Your Own Strategy

The system automatically discovers and registers new strategies. To add your own, create a `.py` file in the `src/app/strategies/` directory and follow the formatting rules.

**Strategy Formatting Rules:**

1.  **Decorators**: The function must be wrapped with `@register_indicator('strategy_name')` and `@njit`.
2.  **Function Signature**:
    *   **Mandatory OHLC Parameters**: The first arguments must be `open: np.ndarray`, `high: np.ndarray`, `low: np.ndarray`, `close: np.ndarray`, `volume: np.ndarray`.
    *   **Indicator Settings**: Any other parameters (e.g., `ema_len: int`, `rsi_len: int`). Data types must be specified.
    *   **Algorithm Flags**: Parameters starting with `flag_` are mutually exclusive. **Only one flag can be `True` in a single combination.**
3.  **Return Value**: The function **must** return a tuple of `(buy, sell)`, where `buy` and `sell` are `np.ndarray` of boolean values.

### Strategy Example (`ohlc_indicator.py`)

```python  
import numpy as np
import vectorbt as vbt
from numba import njit
from .registry import register_indicator

@register_indicator('ohlc')
@njit
def ohlc_indicator(
    open: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray
    ema_len: int = 20,
    rsi_len: int = 14,
    rsi_buy: float = 30,
    rsi_sell: float = 70,
    flag_ema: bool = True,
    flag_sma: bool = False
):
    n = len(close)
    buy = np.zeros(n, dtype=np.bool_)
    sell = np.zeros(n, dtype=np.bool_)

    # ... calculation logic ...

    # Example logic based on EMA
    if flag_ema:
        # A vbt call is needed outside the @njit context if using its indicators,
        # or implement calculations with pure numpy/numba.
        # ema = vbt.IndicatorFactory.from_ta('EMAIndicator').run(close, ema_len).ema_indicator
        # In this example, RSI logic must be implemented inside the function.
        pass # Your logic here

    # Example logic based on SMA
    if flag_sma:
        pass # Your logic here

    # It is critical to return a (buy, sell) tuple
    return buy, sell```

---

## Configuration

### Main Config (`config/config.yaml`)

This file controls the global backtest settings.

```yaml
strategy:
  name: ohlc # Name of the strategy registered in src/app/strategies/
  type:
    long: true # Enable Long positions
    short: true # Enable Short positions
  size:
    use_only_tp_sl: true # Exit trades only on TP/SL
    use_fast: true # Use vectorized calculation for TP/SL combinations
    tp_pct:
      use_fix: false # false: generate combinations from min to max with a step
      fix: 0.05      # true: use a fixed value
      min: 0.01
      max: 0.05
      step: 0.001
    sl_pct:
      # Similar to tp_pct
      use_fix: false
      fix: 0.05
      min: 0.01
      max: 0.05
      step: 0.001
    amount: 10000 # Initial capital
  time:
    start_date: 2025-08-01 # Format: YYYY-MM-DD
    end_date: 2025-08-28
    timeframe: 1h # 1m, 5m, 15m, 1h, 4h, 1d...
  symbols:
    use_all: true # true: test on all USDT futures ON BINANCE (~500), false: use the list below
    symbols:
      - BTCUSDT
	  - ETHUSDT
processor:
  max_processors: 5 # Number of CPU cores for backtesting
  max_chunks: 10    # Number of parameter combinations in one batch for processing
```

### Strategy Config (`config/<strategy_name>_strategy_config.yaml`)

This file is auto-generated on the first run and contains the parameters for your strategy.

-   **multi**: Defines ranges of values for iterating through combinations.
-   **single**: Defines fixed values for a single run.
-   **settings**: `flag_forbidden: true` ensures that at least one `flag_` is active in each combination.

---  

## Usage

The program is operated via a command-line interface.

```bash  
python main.py 
```  

**Available Commands:**

-   `download` - Downloads or updates historical data for the selected symbols and timeframe.
-   `run` - Starts the backtesting process with the parameters from `config.yaml`.
-   `analysis` - Runs an analysis of the saved results, aggregates them, and saves the output to `data/analysis`.
-   `exit` - Exits the program.

---  

## Roadmap

-   [ ] Multi-exchange support (Bybit, OKX, etc.)
-   [ ] Web dashboard with analytics
-   [ ] Spot market support (exchange, )
-  [ ] Add custom TP/SL (break even and trailing stop)

---  

## Contact
[GitHub](https://github.com/sotaireange/cv) | [LinkedIn](https://www.linkedin.com/in/sotaireange/)