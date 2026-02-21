from enum import Enum
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


class MoneyScript(str, Enum):
    avoidance = "money_avoidance"
    worship = "money_worship"
    status = "money_status"
    vigilance = "money_vigilance"


class KMSIResponse(BaseModel):
    avoidance: list[int] = Field(..., min_length=4, max_length=4)
    worship: list[int] = Field(..., min_length=4, max_length=4)
    status: list[int] = Field(..., min_length=4, max_length=4)
    vigilance: list[int] = Field(..., min_length=4, max_length=4)


class ScenarioRequest(BaseModel):
    city: str
    gross_monthly_income: float = Field(..., gt=0)
    rent: float = Field(..., ge=0)
    utilities: float = Field(2100, ge=0)
    transportation: float = Field(1500, ge=0)
    groceries: float = Field(10500, ge=0)
    discretionary: float = Field(6000, ge=0)
    target_savings_rate: float = Field(0.2, ge=0, le=1)


class SubscriptionRequest(BaseModel):
    service_name: str
    monthly_cost: float = Field(..., ge=0)
    cancellation_reason: str = "I no longer use this service"
    user_consent: bool


app = FastAPI(title="Financial Therapy Coach MVP", version="0.1.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "static" / "index.html"
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


QUESTIONNAIRE = {
    "avoidance": [
        "Thinking about money makes me anxious.",
        "I avoid checking account balances.",
        "Budgeting feels overwhelming.",
        "I postpone financial decisions.",
    ],
    "worship": [
        "More money would solve most life problems.",
        "I feel happier when I spend on treats.",
        "I often think a bigger income is the key to peace.",
        "I make purchases to reduce stress quickly.",
    ],
    "status": [
        "People respect me more when I display success.",
        "I compare my lifestyle to peers often.",
        "Owning premium brands is important to me.",
        "I spend to maintain a certain image.",
    ],
    "vigilance": [
        "I feel guilty when I spend on myself.",
        "I closely monitor every expense.",
        "Debt makes me deeply uncomfortable.",
        "I save aggressively even when unnecessary.",
    ],
}


COACHING_TEMPLATES = {
    MoneyScript.avoidance: {
        "tone": "supportive_low_friction",
        "message": "You're doing great. Let's keep this simple: I prepared one tiny action for today—review and approve a single subscription cancellation. Reply with 'yes' to proceed.",
        "homework": "Spend 5 minutes opening your banking app and identify one recurring charge.",
    },
    MoneyScript.worship: {
        "tone": "values_reframing",
        "message": "Let's align spending with your long-term freedom goals. I found an opportunity to redirect impulsive spending into a goal bucket.",
        "homework": "Delay any non-essential purchase for 24 hours and log whether the urge changed.",
    },
    MoneyScript.status: {
        "tone": "identity_and_boundaries",
        "message": "Your financial plan should serve your future self, not social pressure. I built a tradeoff view showing what status spending costs your house fund.",
        "homework": "Choose one social spending boundary for this week and share it with a trusted friend.",
    },
    MoneyScript.vigilance: {
        "tone": "data_reassuring",
        "message": "Your savings rate is strong. Based on your targets, you can safely allocate a small enjoyment budget without delaying retirement.",
        "homework": "Schedule a guilt-free spend (fixed amount) on something meaningful and record your stress before/after.",
    },
}


def _risk_band(score: int) -> str:
    if score >= 33:
        return "active_risk"
    if score >= 25:
        return "at_risk"
    return "stable"


def _infer_primary_script(scores: dict[str, int]) -> MoneyScript:
    key = max(scores, key=scores.get)
    return MoneyScript(f"money_{key}")


def _net_salary_tr_2026(gross_monthly_income: float) -> float:
    sgk = gross_monthly_income * 0.14
    unemployment = gross_monthly_income * 0.01
    tax_base = gross_monthly_income - sgk - unemployment
    annualized = tax_base * 12

    if annualized <= 190000:
        tax_rate = 0.15
    elif annualized <= 400000:
        tax_rate = 0.20
    else:
        tax_rate = 0.27

    income_tax = tax_base * tax_rate
    return round(gross_monthly_income - sgk - unemployment - income_tax, 2)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return INDEX_PATH.read_text(encoding="utf-8")


@app.get("/index.html", response_class=HTMLResponse)
def index_html() -> str:
    return INDEX_PATH.read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/questionnaire")
def questionnaire() -> dict[str, list[str]]:
    return QUESTIONNAIRE


@app.post("/api/profile")
def profile(responses: KMSIResponse) -> dict:
    scores = {
        "avoidance": sum(responses.avoidance),
        "worship": sum(responses.worship),
        "status": sum(responses.status),
        "vigilance": sum(responses.vigilance),
    }
    primary = _infer_primary_script(scores)
    return {
        "scores": scores,
        "risk_bands": {k: _risk_band(v) for k, v in scores.items()},
        "primary_script": primary,
        "coaching": COACHING_TEMPLATES[primary],
    }


@app.post("/api/scenario")
def scenario(payload: ScenarioRequest) -> dict:
    net_salary = _net_salary_tr_2026(payload.gross_monthly_income)
    total_expenses = (
        payload.rent
        + payload.utilities
        + payload.transportation
        + payload.groceries
        + payload.discretionary
    )
    projected_savings = net_salary - total_expenses
    projected_savings_rate = projected_savings / net_salary if net_salary else 0

    return {
        "city": payload.city,
        "net_salary": net_salary,
        "expense_breakdown": {
            "rent": payload.rent,
            "utilities": payload.utilities,
            "transportation": payload.transportation,
            "groceries": payload.groceries,
            "discretionary": payload.discretionary,
            "total": round(total_expenses, 2),
        },
        "projected_savings": round(projected_savings, 2),
        "projected_savings_rate": round(projected_savings_rate, 3),
        "target_savings_rate": payload.target_savings_rate,
        "affordable": projected_savings_rate >= payload.target_savings_rate,
    }


@app.post("/api/subscription/cancel-script")
def cancel_script(payload: SubscriptionRequest) -> dict:
    if not payload.user_consent:
        raise HTTPException(
            status_code=400,
            detail="Explicit consent is required before cancellation workflows.",
        )

    draft = (
        f"Subject: Cancellation request for {payload.service_name}\n\n"
        f"Hello support team,\n\n"
        f"Please cancel my recurring subscription for {payload.service_name} effective immediately. "
        f"Reason: {payload.cancellation_reason}.\n"
        "Please confirm cancellation in writing and ensure no future renewals are processed.\n\n"
        "Thank you."
    )

    return {
        "service_name": payload.service_name,
        "monthly_cost": payload.monthly_cost,
        "annual_savings_if_cancelled": round(payload.monthly_cost * 12, 2),
        "draft_email": draft,
        "next_steps": [
            "Send the request through the same channel used for signup.",
            "Capture confirmation number or screenshot.",
            "Set a 7-day reminder to verify no further charges.",
        ],
    }


@app.get("/{full_path:path}", response_class=HTMLResponse)
def frontend_fallback(full_path: str) -> str:
    if full_path.startswith("api/") or full_path == "api":
        raise HTTPException(status_code=404, detail="Not Found")
    if full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not Found")
    return INDEX_PATH.read_text(encoding="utf-8")
