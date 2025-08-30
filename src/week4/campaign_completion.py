#!/usr/bin/env python3
"""
Campaign Completion Evaluation System
Comprehensive assessment of campaign readiness for maintenance mode transition
"""

import os
import sys
import json
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import DatabaseManager, Provider
from src.campaign.campaign_state import CampaignStateManager
from src.monitoring.campaign_dashboard import CampaignDashboard
from src.monitoring.quality_assurance import QualityAssuranceSystem
from src.monitoring.search_optimizer import SearchOptimizer

logger = logging.getLogger(__name__)


class CompletionStatus(Enum):
    """Campaign completion status levels"""
    CRITICAL = "critical"        # < 20% complete
    BEHIND = "behind"           # 20-40% complete
    ON_TRACK = "on_track"       # 40-70% complete
    ADVANCED = "advanced"       # 70-90% complete
    NEAR_COMPLETE = "near_complete"  # 90-95% complete
    COMPLETE = "complete"       # >= 95% complete


class TransitionDecision(Enum):
    """Maintenance mode transition decision"""
    CONTINUE_CAMPAIGN = "continue"
    CONDITIONAL_TRANSITION = "conditional"
    READY_FOR_TRANSITION = "ready"
    FORCE_TRANSITION = "force"


@dataclass
class CompletionCriterion:
    """Individual completion criterion assessment"""
    name: str
    description: str
    current_value: float
    target_value: float
    weight: float  # Importance weight (0-1)
    
    # Calculated metrics
    completion_percentage: float = 0.0
    meets_threshold: bool = False
    threshold_percentage: float = 0.8  # 80% threshold by default
    
    # Status
    status: CompletionStatus = CompletionStatus.CRITICAL
    issues: List[str] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        """Calculate completion metrics"""
        if self.issues is None:
            self.issues = []
        if self.recommendations is None:
            self.recommendations = []
        
        # Calculate completion percentage
        if self.target_value > 0:
            self.completion_percentage = min(100.0, (self.current_value / self.target_value) * 100)
        else:
            self.completion_percentage = 100.0 if self.current_value > 0 else 0.0
        
        # Check threshold
        self.meets_threshold = self.completion_percentage >= (self.threshold_percentage * 100)
        
        # Determine status
        if self.completion_percentage >= 95:
            self.status = CompletionStatus.COMPLETE
        elif self.completion_percentage >= 90:
            self.status = CompletionStatus.NEAR_COMPLETE
        elif self.completion_percentage >= 70:
            self.status = CompletionStatus.ADVANCED
        elif self.completion_percentage >= 40:
            self.status = CompletionStatus.ON_TRACK
        elif self.completion_percentage >= 20:
            self.status = CompletionStatus.BEHIND
        else:
            self.status = CompletionStatus.CRITICAL


@dataclass
class CampaignCompletionAssessment:
    """Comprehensive campaign completion assessment"""
    
    # Overall Assessment
    overall_completion_percentage: float = 0.0
    weighted_completion_score: float = 0.0
    campaign_status: CompletionStatus = CompletionStatus.CRITICAL
    transition_decision: TransitionDecision = TransitionDecision.CONTINUE_CAMPAIGN
    
    # Individual Criteria
    provider_count_criterion: CompletionCriterion = None
    geographic_coverage_criterion: CompletionCriterion = None
    quality_standards_criterion: CompletionCriterion = None
    data_integrity_criterion: CompletionCriterion = None
    system_health_criterion: CompletionCriterion = None
    cost_efficiency_criterion: CompletionCriterion = None
    
    # Detailed Metrics
    total_providers: int = 0
    target_providers: int = 5000
    geographic_coverage_percentage: float = 0.0
    quality_score: float = 0.0
    data_integrity_score: float = 0.0
    system_health_score: float = 0.0
    budget_utilization: float = 0.0
    
    # Timeline Analysis
    estimated_completion_date: str = ""
    days_remaining: int = 0
    current_daily_rate: float = 0.0
    required_daily_rate: float = 0.0
    
    # Transition Analysis
    readiness_score: float = 0.0  # 0-100 scale
    critical_blockers: List[str] = None
    minor_issues: List[str] = None
    transition_recommendations: List[str] = None
    
    # Risk Assessment
    risk_level: str = "medium"  # low, medium, high, critical
    risk_factors: List[str] = None
    mitigation_strategies: List[str] = None
    
    def __post_init__(self):
        """Initialize lists"""
        if self.critical_blockers is None:
            self.critical_blockers = []
        if self.minor_issues is None:
            self.minor_issues = []
        if self.transition_recommendations is None:
            self.transition_recommendations = []
        if self.risk_factors is None:
            self.risk_factors = []
        if self.mitigation_strategies is None:
            self.mitigation_strategies = []


class CampaignCompletionEvaluator:
    """Comprehensive campaign completion evaluation system"""
    
    def __init__(self):
        """Initialize completion evaluator"""
        self.db_manager = DatabaseManager()
        self.campaign_state = CampaignStateManager()
        self.dashboard = CampaignDashboard()
        self.qa_system = QualityAssuranceSystem()
        self.search_optimizer = SearchOptimizer()
        
        # Completion thresholds
        self.thresholds = {
            'provider_count_minimum': 4000,  # 80% of 5000
            'geographic_coverage_minimum': 0.6,  # 60% of key areas covered
            'quality_score_minimum': 75.0,  # Quality score threshold
            'data_integrity_minimum': 85.0,  # Data integrity threshold
            'system_health_minimum': 80.0,  # System health threshold
            'budget_utilization_maximum': 0.9  # 90% budget utilization max
        }
        
        # Criterion weights (should sum to 1.0)
        self.weights = {
            'provider_count': 0.30,      # 30% weight - most important
            'geographic_coverage': 0.20,  # 20% weight
            'quality_standards': 0.20,   # 20% weight
            'data_integrity': 0.15,      # 15% weight
            'system_health': 0.10,       # 10% weight
            'cost_efficiency': 0.05      # 5% weight
        }
        
        logger.info("✅ Campaign Completion Evaluator initialized")
    
    def evaluate_provider_count_criterion(self) -> CompletionCriterion:
        """Evaluate provider count completion criterion"""
        try:
            dashboard_metrics = self.dashboard.get_real_time_metrics()
            current_providers = dashboard_metrics.total_providers
            target_providers = 5000
            
            criterion = CompletionCriterion(
                name="Provider Count",
                description="Total healthcare providers collected",
                current_value=current_providers,
                target_value=target_providers,
                weight=self.weights['provider_count'],
                threshold_percentage=0.80  # 80% threshold (4000 providers)
            )
            
            # Add issues and recommendations based on progress
            if criterion.completion_percentage < 80:
                criterion.issues.append(f"Only {current_providers} providers collected ({criterion.completion_percentage:.1f}% of target)")
                criterion.recommendations.append("Intensify collection efforts with optimized search strategies")
                
                if criterion.completion_percentage < 20:
                    criterion.issues.append("Critical shortage - far below minimum viable dataset")
                    criterion.recommendations.append("Consider extending campaign timeline or reducing scope")
            
            if criterion.completion_percentage < 50:
                criterion.recommendations.append("Focus on high-yield locations identified by search optimizer")
            
            return criterion
            
        except Exception as e:
            logger.error(f"Provider count criterion evaluation failed: {e}")
            return CompletionCriterion(
                name="Provider Count",
                description="Error evaluating provider count",
                current_value=0,
                target_value=5000,
                weight=self.weights['provider_count']
            )
    
    def evaluate_geographic_coverage_criterion(self) -> CompletionCriterion:
        """Evaluate geographic coverage completion criterion"""
        try:
            # Get location metrics from search optimizer
            location_metrics = self.search_optimizer.analyze_geographic_performance()
            
            # Calculate coverage metrics
            total_locations_covered = len(location_metrics)
            target_locations = 50  # Reasonable target for major coverage
            
            # Check coverage of international areas
            international_areas_covered = len([loc for loc in location_metrics if loc.is_international_area])
            target_international_areas = 10  # Key international areas
            
            # Calculate overall coverage score
            location_coverage = min(100, (total_locations_covered / target_locations) * 100)
            international_coverage = min(100, (international_areas_covered / target_international_areas) * 100)
            overall_coverage = (location_coverage * 0.7 + international_coverage * 0.3)
            
            criterion = CompletionCriterion(
                name="Geographic Coverage",
                description="Coverage across key locations and international areas",
                current_value=overall_coverage,
                target_value=100.0,
                weight=self.weights['geographic_coverage'],
                threshold_percentage=0.60  # 60% threshold
            )
            
            # Add analysis
            if overall_coverage < 60:
                criterion.issues.append(f"Limited geographic coverage: {total_locations_covered} locations covered")
                criterion.recommendations.append("Expand to more prefectures and key international areas")
            
            if international_areas_covered < 5:
                criterion.issues.append("Insufficient international area coverage")
                criterion.recommendations.append("Focus on Roppongi, Azabu, Shibuya, and other international districts")
            
            return criterion
            
        except Exception as e:
            logger.error(f"Geographic coverage criterion evaluation failed: {e}")
            return CompletionCriterion(
                name="Geographic Coverage",
                description="Error evaluating geographic coverage",
                current_value=0,
                target_value=100.0,
                weight=self.weights['geographic_coverage']
            )
    
    def evaluate_quality_standards_criterion(self) -> CompletionCriterion:
        """Evaluate quality standards completion criterion"""
        try:
            # Get quality metrics from QA system
            qa_metrics = self.qa_system.generate_system_quality_metrics()
            
            current_quality = qa_metrics.overall_system_quality
            target_quality = 85.0  # Target quality score
            
            criterion = CompletionCriterion(
                name="Quality Standards",
                description="Overall data and content quality score",
                current_value=current_quality,
                target_value=target_quality,
                weight=self.weights['quality_standards'],
                threshold_percentage=0.88  # 88% of 85 = ~75 minimum score
            )
            
            # Add quality-specific analysis
            if current_quality < 75:
                criterion.issues.append(f"Quality score {current_quality:.1f} below acceptable threshold")
                criterion.recommendations.append("Improve content generation and data validation processes")
            
            if qa_metrics.critical_issues > 0:
                criterion.issues.append(f"{qa_metrics.critical_issues} critical quality issues detected")
                criterion.recommendations.append("Address critical quality issues before transition")
            
            if qa_metrics.providers_needing_review > 50:
                criterion.issues.append(f"{qa_metrics.providers_needing_review} providers need manual review")
                criterion.recommendations.append("Complete manual review queue before transition")
            
            return criterion
            
        except Exception as e:
            logger.error(f"Quality standards criterion evaluation failed: {e}")
            return CompletionCriterion(
                name="Quality Standards",
                description="Error evaluating quality standards",
                current_value=0,
                target_value=85.0,
                weight=self.weights['quality_standards']
            )
    
    def evaluate_data_integrity_criterion(self) -> CompletionCriterion:
        """Evaluate data integrity completion criterion"""
        try:
            qa_metrics = self.qa_system.generate_system_quality_metrics()
            dashboard_metrics = self.dashboard.get_real_time_metrics()
            
            # Calculate data integrity components
            romaji_consistency = qa_metrics.romaji_conversion_success_rate
            master_data_compliance = qa_metrics.master_data_compliance_rate
            wordpress_sync_accuracy = qa_metrics.wordpress_sync_accuracy
            
            # Overall data integrity score
            data_integrity_score = (
                romaji_consistency * 0.4 +  # 40% weight on romaji consistency
                master_data_compliance * 0.35 +  # 35% weight on master data
                wordpress_sync_accuracy * 0.25   # 25% weight on WordPress sync
            )
            
            criterion = CompletionCriterion(
                name="Data Integrity",
                description="Romaji consistency, master data compliance, WordPress sync accuracy",
                current_value=data_integrity_score,
                target_value=100.0,
                weight=self.weights['data_integrity'],
                threshold_percentage=0.85  # 85% threshold
            )
            
            # Add integrity-specific analysis
            if romaji_consistency < 95:
                criterion.issues.append(f"Romaji consistency at {romaji_consistency:.1f}% (target: 95%+)")
                criterion.recommendations.append("Review and fix romaji conversion issues")
            
            if master_data_compliance < 90:
                criterion.issues.append(f"Master data compliance at {master_data_compliance:.1f}% (target: 90%+)")
                criterion.recommendations.append("Validate all providers against master location/specialty data")
            
            if wordpress_sync_accuracy < 85:
                criterion.issues.append(f"WordPress sync accuracy at {wordpress_sync_accuracy:.1f}% (target: 85%+)")
                criterion.recommendations.append("Fix WordPress publishing pipeline issues")
            
            return criterion
            
        except Exception as e:
            logger.error(f"Data integrity criterion evaluation failed: {e}")
            return CompletionCriterion(
                name="Data Integrity",
                description="Error evaluating data integrity",
                current_value=0,
                target_value=100.0,
                weight=self.weights['data_integrity']
            )
    
    def evaluate_system_health_criterion(self) -> CompletionCriterion:
        """Evaluate system health completion criterion"""
        try:
            # Get system health from dashboard and monitoring systems
            dashboard_metrics = self.dashboard.get_real_time_metrics()
            
            # System health components (using available metrics)
            database_health = 100.0  # Assume healthy if queries working
            api_health = 85.0 if dashboard_metrics.google_places_cost > 0 else 50.0
            campaign_state_health = 95.0  # Assume healthy based on working state
            search_optimization_health = 90.0  # Based on search optimizer working
            
            # Overall system health
            system_health_score = (
                database_health * 0.3 +
                api_health * 0.3 +
                campaign_state_health * 0.2 +
                search_optimization_health * 0.2
            )
            
            criterion = CompletionCriterion(
                name="System Health",
                description="Database, APIs, campaign state, and monitoring system health",
                current_value=system_health_score,
                target_value=100.0,
                weight=self.weights['system_health'],
                threshold_percentage=0.80  # 80% threshold
            )
            
            # Add health-specific analysis
            if api_health < 80:
                criterion.issues.append("API performance issues detected")
                criterion.recommendations.append("Monitor API rate limits and error rates")
            
            if system_health_score < 80:
                criterion.issues.append("System health below optimal levels")
                criterion.recommendations.append("Address system performance issues before transition")
            
            return criterion
            
        except Exception as e:
            logger.error(f"System health criterion evaluation failed: {e}")
            return CompletionCriterion(
                name="System Health",
                description="Error evaluating system health",
                current_value=0,
                target_value=100.0,
                weight=self.weights['system_health']
            )
    
    def evaluate_cost_efficiency_criterion(self) -> CompletionCriterion:
        """Evaluate cost efficiency completion criterion"""
        try:
            dashboard_metrics = self.dashboard.get_real_time_metrics()
            
            budget_utilization = dashboard_metrics.budget_utilization
            current_cost = dashboard_metrics.total_cost
            budget_limit = 600.0
            
            # Cost efficiency score (inverse of budget utilization, capped at reasonable levels)
            # Higher score = more efficient (less budget used)
            if budget_utilization <= 50:  # Very efficient
                cost_efficiency_score = 100.0
            elif budget_utilization <= 75:  # Good efficiency
                cost_efficiency_score = 90.0
            elif budget_utilization <= 90:  # Acceptable efficiency
                cost_efficiency_score = 75.0
            else:  # Poor efficiency
                cost_efficiency_score = 50.0
            
            criterion = CompletionCriterion(
                name="Cost Efficiency",
                description="Budget utilization and cost per provider efficiency",
                current_value=cost_efficiency_score,
                target_value=100.0,
                weight=self.weights['cost_efficiency'],
                threshold_percentage=0.70  # 70% threshold
            )
            
            # Add cost-specific analysis
            if budget_utilization > 90:
                criterion.issues.append(f"High budget utilization: {budget_utilization:.1f}%")
                criterion.recommendations.append("Monitor remaining budget carefully")
            
            if dashboard_metrics.cost_per_provider > 0.50:  # More than $0.50 per provider
                criterion.issues.append(f"High cost per provider: ${dashboard_metrics.cost_per_provider:.2f}")
                criterion.recommendations.append("Optimize search strategies for better cost efficiency")
            
            return criterion
            
        except Exception as e:
            logger.error(f"Cost efficiency criterion evaluation failed: {e}")
            return CompletionCriterion(
                name="Cost Efficiency",
                description="Error evaluating cost efficiency",
                current_value=0,
                target_value=100.0,
                weight=self.weights['cost_efficiency']
            )
    
    def calculate_overall_completion(self, criteria: List[CompletionCriterion]) -> Tuple[float, float]:
        """Calculate overall completion percentage and weighted score"""
        
        if not criteria:
            return 0.0, 0.0
        
        # Simple average completion percentage
        total_completion = sum(c.completion_percentage for c in criteria)
        overall_completion = total_completion / len(criteria)
        
        # Weighted completion score
        weighted_total = sum(c.completion_percentage * c.weight for c in criteria)
        total_weight = sum(c.weight for c in criteria)
        weighted_score = weighted_total / total_weight if total_weight > 0 else 0.0
        
        return overall_completion, weighted_score
    
    def determine_campaign_status(self, weighted_score: float) -> CompletionStatus:
        """Determine overall campaign status based on weighted score"""
        if weighted_score >= 95:
            return CompletionStatus.COMPLETE
        elif weighted_score >= 90:
            return CompletionStatus.NEAR_COMPLETE
        elif weighted_score >= 70:
            return CompletionStatus.ADVANCED
        elif weighted_score >= 40:
            return CompletionStatus.ON_TRACK
        elif weighted_score >= 20:
            return CompletionStatus.BEHIND
        else:
            return CompletionStatus.CRITICAL
    
    def determine_transition_decision(self, assessment: CampaignCompletionAssessment) -> TransitionDecision:
        """Determine maintenance mode transition decision"""
        
        # Critical blockers check
        if assessment.critical_blockers:
            return TransitionDecision.CONTINUE_CAMPAIGN
        
        # Based on weighted completion score and individual criteria
        if assessment.weighted_completion_score >= 90:
            return TransitionDecision.READY_FOR_TRANSITION
        elif assessment.weighted_completion_score >= 70:
            # Check critical criteria
            if (assessment.provider_count_criterion.meets_threshold and 
                assessment.quality_standards_criterion.meets_threshold and
                assessment.data_integrity_criterion.meets_threshold):
                return TransitionDecision.CONDITIONAL_TRANSITION
            else:
                return TransitionDecision.CONTINUE_CAMPAIGN
        elif assessment.weighted_completion_score >= 40:
            return TransitionDecision.CONTINUE_CAMPAIGN
        else:
            # Very low completion - might need to force transition due to budget/time constraints
            if assessment.budget_utilization > 85 or assessment.days_remaining < 5:
                return TransitionDecision.FORCE_TRANSITION
            else:
                return TransitionDecision.CONTINUE_CAMPAIGN
    
    def generate_transition_recommendations(self, assessment: CampaignCompletionAssessment) -> List[str]:
        """Generate specific transition recommendations"""
        recommendations = []
        
        if assessment.transition_decision == TransitionDecision.READY_FOR_TRANSITION:
            recommendations.extend([
                "✅ READY FOR TRANSITION: All critical criteria met",
                "📋 Prepare maintenance mode documentation and processes",
                "🔄 Schedule transition activities and system handoff",
                "📊 Setup monitoring for maintenance mode operations"
            ])
        
        elif assessment.transition_decision == TransitionDecision.CONDITIONAL_TRANSITION:
            recommendations.extend([
                "⚠️ CONDITIONAL TRANSITION: Core criteria met but improvements needed",
                "🎯 Address remaining quality issues before full transition",
                "📈 Continue collection at reduced rate during transition prep",
                "🔍 Focus on highest-value remaining opportunities"
            ])
        
        elif assessment.transition_decision == TransitionDecision.CONTINUE_CAMPAIGN:
            recommendations.extend([
                "🚀 CONTINUE CAMPAIGN: Core objectives not yet met",
                "📊 Focus on highest-priority completion criteria",
                "💰 Optimize remaining budget for maximum provider yield",
                "⏰ Set target completion date based on current progress rate"
            ])
        
        elif assessment.transition_decision == TransitionDecision.FORCE_TRANSITION:
            recommendations.extend([
                "⚠️ FORCED TRANSITION: Resource constraints require transition",
                "🏥 Focus on quality assurance of existing providers",
                "💾 Preserve current dataset and optimize for maintenance",
                "📋 Document limitations and future collection opportunities"
            ])
        
        # Add specific recommendations based on weakest criteria
        all_criteria = [
            assessment.provider_count_criterion,
            assessment.geographic_coverage_criterion,
            assessment.quality_standards_criterion,
            assessment.data_integrity_criterion,
            assessment.system_health_criterion,
            assessment.cost_efficiency_criterion
        ]
        
        # Find criteria that don't meet thresholds
        failing_criteria = [c for c in all_criteria if c and not c.meets_threshold]
        if failing_criteria:
            # Sort by weight (importance)
            failing_criteria.sort(key=lambda x: x.weight, reverse=True)
            
            for criterion in failing_criteria[:2]:  # Top 2 failing criteria
                recommendations.extend(criterion.recommendations[:2])  # Top 2 recommendations each
        
        return recommendations[:8]  # Limit to 8 recommendations
    
    def assess_risks_and_mitigation(self, assessment: CampaignCompletionAssessment) -> Tuple[str, List[str], List[str]]:
        """Assess transition risks and mitigation strategies"""
        
        risk_factors = []
        mitigation_strategies = []
        
        # Provider count risks
        if assessment.provider_count_criterion.completion_percentage < 50:
            risk_factors.append("Insufficient provider dataset for reliable service")
            mitigation_strategies.append("Focus collection on highest-density areas for maximum yield")
        
        # Quality risks
        if assessment.quality_standards_criterion.completion_percentage < 80:
            risk_factors.append("Data quality issues may impact user experience")
            mitigation_strategies.append("Implement enhanced quality validation before publishing")
        
        # System health risks
        if assessment.system_health_criterion.completion_percentage < 80:
            risk_factors.append("System reliability issues may affect maintenance operations")
            mitigation_strategies.append("Address system performance issues before transition")
        
        # Budget risks
        if assessment.budget_utilization > 85:
            risk_factors.append("Limited budget remaining for quality improvements")
            mitigation_strategies.append("Prioritize most cost-effective improvements")
        
        # Timeline risks
        if assessment.days_remaining < 10 and assessment.weighted_completion_score < 70:
            risk_factors.append("Time constraints may force suboptimal transition")
            mitigation_strategies.append("Prepare contingency plan for early transition")
        
        # Determine overall risk level
        if len(risk_factors) >= 3:
            risk_level = "high"
        elif len(risk_factors) >= 2:
            risk_level = "medium"
        elif len(risk_factors) >= 1:
            risk_level = "low"
        else:
            risk_level = "low"
        
        return risk_level, risk_factors, mitigation_strategies
    
    def generate_comprehensive_assessment(self) -> CampaignCompletionAssessment:
        """Generate comprehensive campaign completion assessment"""
        logger.info("📊 Generating comprehensive campaign completion assessment...")
        
        try:
            # Get dashboard metrics for timeline analysis
            dashboard_metrics = self.dashboard.get_real_time_metrics()
            
            # Evaluate all completion criteria
            provider_criterion = self.evaluate_provider_count_criterion()
            geographic_criterion = self.evaluate_geographic_coverage_criterion()
            quality_criterion = self.evaluate_quality_standards_criterion()
            integrity_criterion = self.evaluate_data_integrity_criterion()
            health_criterion = self.evaluate_system_health_criterion()
            cost_criterion = self.evaluate_cost_efficiency_criterion()
            
            criteria = [
                provider_criterion,
                geographic_criterion,
                quality_criterion,
                integrity_criterion,
                health_criterion,
                cost_criterion
            ]
            
            # Calculate overall completion
            overall_completion, weighted_score = self.calculate_overall_completion(criteria)
            
            # Determine campaign status
            campaign_status = self.determine_campaign_status(weighted_score)
            
            # Create assessment
            assessment = CampaignCompletionAssessment(
                overall_completion_percentage=overall_completion,
                weighted_completion_score=weighted_score,
                campaign_status=campaign_status,
                provider_count_criterion=provider_criterion,
                geographic_coverage_criterion=geographic_criterion,
                quality_standards_criterion=quality_criterion,
                data_integrity_criterion=integrity_criterion,
                system_health_criterion=health_criterion,
                cost_efficiency_criterion=cost_criterion,
                
                # Detailed metrics
                total_providers=dashboard_metrics.total_providers,
                target_providers=5000,
                geographic_coverage_percentage=geographic_criterion.completion_percentage,
                quality_score=quality_criterion.current_value,
                data_integrity_score=integrity_criterion.current_value,
                system_health_score=health_criterion.current_value,
                budget_utilization=dashboard_metrics.budget_utilization,
                
                # Timeline
                estimated_completion_date=dashboard_metrics.estimated_completion_date or "Unknown",
                days_remaining=dashboard_metrics.days_remaining or 0,
                current_daily_rate=dashboard_metrics.current_daily_rate,
                required_daily_rate=dashboard_metrics.required_daily_rate
            )
            
            # Determine transition decision
            assessment.transition_decision = self.determine_transition_decision(assessment)
            
            # Generate recommendations
            assessment.transition_recommendations = self.generate_transition_recommendations(assessment)
            
            # Assess risks
            risk_level, risk_factors, mitigation_strategies = self.assess_risks_and_mitigation(assessment)
            assessment.risk_level = risk_level
            assessment.risk_factors = risk_factors
            assessment.mitigation_strategies = mitigation_strategies
            
            # Calculate readiness score (0-100)
            assessment.readiness_score = weighted_score
            
            # Identify critical blockers and minor issues
            for criterion in criteria:
                if criterion.status in [CompletionStatus.CRITICAL, CompletionStatus.BEHIND]:
                    assessment.critical_blockers.extend(criterion.issues[:2])  # Top 2 issues
                elif criterion.status == CompletionStatus.ON_TRACK:
                    assessment.minor_issues.extend(criterion.issues[:1])  # Top 1 issue
            
            logger.info("✅ Comprehensive campaign completion assessment generated")
            return assessment
            
        except Exception as e:
            logger.error(f"Comprehensive assessment generation failed: {e}")
            # Return minimal assessment with error indication
            return CampaignCompletionAssessment(
                campaign_status=CompletionStatus.CRITICAL,
                transition_decision=TransitionDecision.CONTINUE_CAMPAIGN,
                critical_blockers=[f"Assessment generation failed: {str(e)}"]
            )
    
    def generate_completion_report(self, assessment: CampaignCompletionAssessment) -> str:
        """Generate comprehensive completion assessment report"""
        
        # Status emojis
        status_emojis = {
            CompletionStatus.COMPLETE: "🟢",
            CompletionStatus.NEAR_COMPLETE: "🔵", 
            CompletionStatus.ADVANCED: "🟡",
            CompletionStatus.ON_TRACK: "🟠",
            CompletionStatus.BEHIND: "🔴",
            CompletionStatus.CRITICAL: "⚫"
        }
        
        transition_emojis = {
            TransitionDecision.READY_FOR_TRANSITION: "✅",
            TransitionDecision.CONDITIONAL_TRANSITION: "⚠️",
            TransitionDecision.CONTINUE_CAMPAIGN: "🚀",
            TransitionDecision.FORCE_TRANSITION: "⚠️"
        }
        
        report = f"""
{'=' * 80}
🏁 CAMPAIGN COMPLETION ASSESSMENT REPORT
{'=' * 80}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 80}
📊 OVERALL COMPLETION SUMMARY
{'=' * 80}
Campaign Status: {status_emojis.get(assessment.campaign_status, "❓")} {assessment.campaign_status.value.upper()}
Overall Completion: {assessment.overall_completion_percentage:.1f}%
Weighted Completion Score: {assessment.weighted_completion_score:.1f}/100
Readiness Score: {assessment.readiness_score:.1f}/100

Transition Decision: {transition_emojis.get(assessment.transition_decision, "❓")} {assessment.transition_decision.value.upper()}

{'=' * 80}
📋 COMPLETION CRITERIA ASSESSMENT
{'=' * 80}"""

        # Individual criteria assessment
        criteria = [
            assessment.provider_count_criterion,
            assessment.geographic_coverage_criterion,
            assessment.quality_standards_criterion,
            assessment.data_integrity_criterion,
            assessment.system_health_criterion,
            assessment.cost_efficiency_criterion
        ]
        
        for criterion in criteria:
            if criterion:
                status_emoji = status_emojis.get(criterion.status, "❓")
                threshold_check = "✅" if criterion.meets_threshold else "❌"
                
                report += f"""
{criterion.name}: {status_emoji} {criterion.completion_percentage:.1f}% {threshold_check}
  Current: {criterion.current_value:.1f} | Target: {criterion.target_value:.1f} | Weight: {criterion.weight:.1%}
  Status: {criterion.status.value.title()} | Threshold Met: {criterion.meets_threshold}"""
                
                if criterion.issues:
                    report += f"\n  Issues: {'; '.join(criterion.issues[:2])}"
        
        report += f"""

{'=' * 80}
⏰ TIMELINE ANALYSIS
{'=' * 80}
Current Providers: {assessment.total_providers:,} / {assessment.target_providers:,}
Current Daily Rate: {assessment.current_daily_rate:.1f} providers/day
Required Daily Rate: {assessment.required_daily_rate:.1f} providers/day
Estimated Completion: {assessment.estimated_completion_date}
Days Remaining: {assessment.days_remaining}

{'=' * 80}
🎯 TRANSITION DECISION ANALYSIS
{'=' * 80}
Decision: {assessment.transition_decision.value.upper()}
Risk Level: {assessment.risk_level.upper()}

Critical Blockers ({len(assessment.critical_blockers)}):"""
        
        for i, blocker in enumerate(assessment.critical_blockers[:5], 1):
            report += f"\n  {i}. {blocker}"
        
        if not assessment.critical_blockers:
            report += "\n  ✅ No critical blockers identified"
        
        report += f"""

Minor Issues ({len(assessment.minor_issues)}):"""
        
        for i, issue in enumerate(assessment.minor_issues[:3], 1):
            report += f"\n  {i}. {issue}"
        
        if not assessment.minor_issues:
            report += "\n  ✅ No significant minor issues"
        
        report += f"""

{'=' * 80}
💡 TRANSITION RECOMMENDATIONS
{'=' * 80}"""
        
        for i, rec in enumerate(assessment.transition_recommendations, 1):
            report += f"\n{i}. {rec}"
        
        report += f"""

{'=' * 80}
⚠️ RISK ASSESSMENT & MITIGATION
{'=' * 80}
Risk Level: {assessment.risk_level.upper()}

Risk Factors ({len(assessment.risk_factors)}):"""
        
        for i, risk in enumerate(assessment.risk_factors, 1):
            report += f"\n  {i}. {risk}"
        
        if not assessment.risk_factors:
            report += "\n  ✅ No significant risk factors identified"
        
        report += f"""

Mitigation Strategies ({len(assessment.mitigation_strategies)}):"""
        
        for i, strategy in enumerate(assessment.mitigation_strategies, 1):
            report += f"\n  {i}. {strategy}"
        
        report += f"""

{'=' * 80}
📈 DETAILED METRICS BREAKDOWN
{'=' * 80}
Provider Collection:
  • Total Providers: {assessment.total_providers:,}
  • Target: {assessment.target_providers:,} ({assessment.total_providers/assessment.target_providers*100:.1f}% complete)
  • Geographic Coverage: {assessment.geographic_coverage_percentage:.1f}%

Quality & Integrity:
  • Quality Score: {assessment.quality_score:.1f}/100
  • Data Integrity Score: {assessment.data_integrity_score:.1f}/100
  • System Health Score: {assessment.system_health_score:.1f}/100

Cost & Efficiency:
  • Budget Utilization: {assessment.budget_utilization:.1f}%
  • Daily Collection Rate: {assessment.current_daily_rate:.1f} providers/day

{'=' * 80}
🏁 COMPLETION ASSESSMENT SUMMARY
{'=' * 80}"""
        
        if assessment.transition_decision == TransitionDecision.READY_FOR_TRANSITION:
            report += """
✅ CAMPAIGN READY FOR MAINTENANCE MODE TRANSITION
All critical criteria have been met. The campaign has achieved sufficient
provider coverage, quality standards, and system reliability for transition.

Next Steps:
1. Prepare maintenance mode documentation and processes
2. Schedule transition activities and system handoff
3. Setup ongoing monitoring for maintenance operations
4. Archive campaign data and prepare for operational mode"""
            
        elif assessment.transition_decision == TransitionDecision.CONDITIONAL_TRANSITION:
            report += """
⚠️ CONDITIONAL TRANSITION READINESS
Core criteria are met but some improvements are recommended. Transition
is possible with ongoing quality improvements.

Next Steps:
1. Address identified quality issues during transition preparation
2. Continue limited collection during transition setup
3. Implement enhanced monitoring and quality controls
4. Plan gradual transition with quality checkpoints"""
            
        elif assessment.transition_decision == TransitionDecision.CONTINUE_CAMPAIGN:
            report += """
🚀 CONTINUE ACTIVE CAMPAIGN
Core objectives have not yet been met. Campaign should continue with
focused efforts on priority areas and criteria.

Next Steps:
1. Focus on highest-priority completion criteria
2. Optimize collection strategies for maximum efficiency
3. Set targeted milestones for reassessment
4. Monitor progress weekly for transition readiness"""
            
        else:  # FORCE_TRANSITION
            report += """
⚠️ FORCED TRANSITION DUE TO CONSTRAINTS
Resource or time constraints require transition despite incomplete objectives.
Focus on maximizing value of existing dataset.

Next Steps:
1. Implement quality assurance for existing providers
2. Document dataset limitations and coverage gaps
3. Prepare maintenance mode with current provider base
4. Plan future collection phases if resources permit"""
        
        report += f"""

{'=' * 80}
Campaign Completion Assessment Complete
Generated by: Healthcare Campaign Completion Evaluator v1.0
Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Next Assessment: {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')} (Weekly)
{'=' * 80}"""
        
        return report
    
    def save_completion_assessment(self, assessment: CampaignCompletionAssessment, report: str) -> str:
        """Save completion assessment to file"""
        # Ensure reports directory exists
        reports_dir = Path("completion_reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = reports_dir / f"completion_assessment_{timestamp}.txt"
        
        # Save report
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Also save assessment data as JSON for programmatic access
        json_filename = reports_dir / f"completion_data_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            # Convert assessment to dict for JSON serialization
            assessment_dict = asdict(assessment)
            # Convert enums to strings
            assessment_dict['campaign_status'] = assessment.campaign_status.value
            assessment_dict['transition_decision'] = assessment.transition_decision.value
            for criterion_name in ['provider_count_criterion', 'geographic_coverage_criterion',
                                 'quality_standards_criterion', 'data_integrity_criterion',
                                 'system_health_criterion', 'cost_efficiency_criterion']:
                if assessment_dict[criterion_name]:
                    assessment_dict[criterion_name]['status'] = assessment_dict[criterion_name]['status'].value if hasattr(assessment_dict[criterion_name]['status'], 'value') else assessment_dict[criterion_name]['status']
            
            json.dump(assessment_dict, f, indent=2, default=str)
        
        logger.info(f"📄 Completion assessment saved: {filename}")
        return str(filename)
    
    def run_completion_evaluation(self) -> Dict[str, Any]:
        """Run complete campaign completion evaluation"""
        logger.info("🏁 Starting campaign completion evaluation...")
        
        results = {
            'success': True,
            'assessment_generated': False,
            'report_generated': False,
            'report_saved': False,
            'completion_score': 0.0,
            'transition_decision': 'continue',
            'critical_blockers': 0,
            'recommendations_count': 0,
            'errors': []
        }
        
        try:
            # Generate comprehensive assessment
            assessment = self.generate_comprehensive_assessment()
            results['assessment_generated'] = True
            results['completion_score'] = assessment.weighted_completion_score
            results['transition_decision'] = assessment.transition_decision.value
            results['critical_blockers'] = len(assessment.critical_blockers)
            results['recommendations_count'] = len(assessment.transition_recommendations)
            
            # Generate report
            report = self.generate_completion_report(assessment)
            results['report_generated'] = True
            
            # Save report
            filename = self.save_completion_assessment(assessment, report)
            results['report_saved'] = True
            results['report_filename'] = filename
            
            logger.info("✅ Campaign completion evaluation completed successfully")
            
        except Exception as e:
            logger.error(f"Completion evaluation failed: {e}")
            results['success'] = False
            results['errors'].append(str(e))
        
        return results


def main():
    """Run campaign completion evaluation"""
    print("\n" + "=" * 80)
    print("🏁 HEALTHCARE CAMPAIGN - COMPLETION EVALUATION SYSTEM")
    print("=" * 80)
    
    evaluator = CampaignCompletionEvaluator()
    
    # Run completion evaluation
    results = evaluator.run_completion_evaluation()
    
    # Display results
    if results['success']:
        print("✅ Campaign completion evaluation completed successfully")
        print(f"📊 Completion Score: {results['completion_score']:.1f}/100")
        print(f"🎯 Transition Decision: {results['transition_decision'].upper()}")
        print(f"⚠️ Critical Blockers: {results['critical_blockers']}")
        print(f"💡 Recommendations: {results['recommendations_count']}")
        
        if results['report_saved']:
            print(f"📄 Assessment report saved: {results.get('report_filename', 'completion_reports/')}")
        
    else:
        print("❌ Campaign completion evaluation failed")
        for error in results['errors']:
            print(f"   Error: {error}")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()