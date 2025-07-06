#!/usr/bin/env python3
"""
Flask Review Dashboard
Provides a bare-bones interface for reviewing and editing provider data, and tracking metrics.
"""

from flask import Flask, render_template, request
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True)
    provider_name = Column(String(255), nullable=False)
    address = Column(Text)
    city = Column(String(100))
    english_proficiency = Column(String(50))
    review_highlights = Column(JSON)
    ai_description = Column(Text)
    status = Column(String(50), default="pending")

class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True)
    timestamp = Column(String)
    metric_type = Column(String(50))
    value = Column(Float)
    details = Column(JSON)

app = Flask(__name__)
engine = create_engine(f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:5432/directory")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

@app.route("/review", methods=["GET", "POST"])
def review_providers():
    session = Session()
    filter_type = request.args.get("filter", "pending")
    if filter_type == "unknown_proficiency":
        providers = session.query(Provider).filter_by(english_proficiency="Unknown").limit(50).all()
    else:
        providers = session.query(Provider).filter_by(status="pending").limit(50).all()
    if request.method == "POST":
        provider_id = request.form["id"]
        action = request.form["action"]
        provider = session.query(Provider).get(provider_id)
        if action == "edit":
            provider.ai_description = request.form["ai_description"]
            provider.english_proficiency = request.form["english_proficiency"]
            session.commit()
        elif action == "approve":
            provider.status = "approved"
            session.commit()
        elif action == "reject":
            provider.status = "rejected"
            session.commit()
    session.close()
    return render_template("review.html", providers=providers, filter_type=filter_type)

@app.route("/metrics")
def metrics_dashboard():
    session = Session()
    total_providers = session.query(Provider).count()
    api_calls = session.query(Metric).filter_by(metric_type="api_calls").all()
    total_calls = sum(m.value for m in api_calls)
    total_cost = sum(m.details["estimated_cost"] for m in api_calls)
    providers_added = session.query(Metric).filter_by(metric_type="providers_added").all()
    daily_progress = providers_added[-1].value if providers_added else 0
    session.close()
    return render_template("metrics.html", metrics={
        "total_providers": total_providers,
        "total_api_calls": total_calls,
        "estimated_cost": total_cost,
        "daily_progress": daily_progress,
        "remaining_providers": 5000 - total_providers
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)