from fastapi import APIRouter
from data.database import DataDB
from technicals.indicators import Donchian
import pandas as pd

router = APIRouter()


@router.get("/donchian/{pair}/{granularity}/{count}/{window}")
def indicator_donchian(pair: str, granularity: str, count: int, window: int):
    db = DataDB()
    df = pd.DataFrame(db.query_all(f"{pair}_{granularity}", count))
    df = Donchian(df, window).dropna().reset_index(drop=True)
    return {"donchian": df.to_dict("list")}
