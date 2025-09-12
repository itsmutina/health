from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count, Max, Min
from django.template.loader import render_to_string
from django.conf import settings
import json
import uuid
from datetime import datetime, timedelta
from .models import Report, ReportAccess
from journal.models import JournalEntry, EntryEmotion, EntryActivity


class ReportsView(LoginRequiredMixin, TemplateView):
    """Main reports view."""
    template_name = 'reports/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's reports
        context['reports'] = user.reports.all()[:20]  # Last 20 reports
        
        return context


class GenerateReportView(LoginRequiredMixin, View):
    """Generate a new report."""
    
    def post(self, request):
        """Generate report based on date range."""
        try:
            data = json.loads(request.body)
            user = request.user
            
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            report_type = data.get('report_type', 'custom')
            
            # Get entries for the date range
            entries = user.entries.filter(
                date__gte=start_date,
                date__lte=end_date
            ).order_by('date')
            
            if not entries.exists():
                return JsonResponse({'success': False, 'message': 'No data found for the selected date range'})
            
            # Generate report data
            report_data = self.generate_report_data(user, entries, start_date, end_date)
            
            # Create report
            report = Report.objects.create(
                user=user,
                title=f"{report_type.title()} Report - {start_date} to {end_date}",
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                data=report_data,
                share_expires_at=timezone.now() + timedelta(days=7)  # 7 days expiry
            )
            
            # Generate PDF
            try:
                pdf_content = self.generate_pdf(report_data, user, start_date, end_date)
                report.pdf_file.save(f'report_{report.id}.pdf', pdf_content, save=True)
                print(f"PDF generated successfully for report {report.id}")
            except Exception as e:
                print(f"Error generating PDF for report {report.id}: {str(e)}")
                import traceback
                traceback.print_exc()
            
            return JsonResponse({
                'success': True,
                'report_id': report.id,
                'share_url': f'/reports/share/{report.share_token}/',
                'download_url': f'/reports/download/{report.id}/'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    def generate_report_data(self, user, entries, start_date, end_date):
        """Generate comprehensive report data."""
        data = {
            'summary': {
                'total_entries': entries.count(),
                'date_range': f"{start_date} to {end_date}",
                'days_tracked': (end_date - start_date).days + 1,
            },
            'mood': {
                'average': round(entries.aggregate(avg=Avg('mood_rating'))['avg'] or 0, 2),
                'highest': entries.aggregate(max=Max('mood_rating'))['max'] or 0,
                'lowest': entries.aggregate(min=Min('mood_rating'))['min'] or 0,
                'trend': self.calculate_trend([e.mood_rating for e in entries]),
            },
            'stress': {
                'average': round(entries.aggregate(avg=Avg('stress_level'))['avg'] or 0, 2),
                'entries_with_stress': entries.exclude(stress_level__isnull=True).count(),
            },
            'sleep': {
                'average': round(entries.aggregate(avg=Avg('sleep_hours'))['avg'] or 0, 2),
                'entries_with_sleep': entries.exclude(sleep_hours__isnull=True).count(),
            },
            'emotions': self.get_emotion_stats(entries),
            'activities': self.get_activity_stats(entries),
            'entries': []
        }
        
        # Add individual entries
        for entry in entries:
            data['entries'].append({
                'date': entry.date.isoformat(),
                'mood_rating': entry.mood_rating,
                'stress_level': entry.stress_level,
                'sleep_hours': entry.sleep_hours,
                'notes': entry.notes,
                'emotions': [e.emotion.name for e in entry.emotions.all()],
                'activities': [a.activity.name for a in entry.activities.all()],
            })
        
        return data
    
    def get_emotion_stats(self, entries):
        """Get emotion statistics."""
        emotion_counts = {}
        for entry in entries:
            for emotion in entry.emotions.all():
                emotion_counts[emotion.emotion.name] = emotion_counts.get(emotion.emotion.name, 0) + 1
        
        return sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
    
    def get_activity_stats(self, entries):
        """Get activity statistics."""
        activity_counts = {}
        for entry in entries:
            for activity in entry.activities.all():
                activity_counts[activity.activity.name] = activity_counts.get(activity.activity.name, 0) + 1
        
        return sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)
    
    def calculate_trend(self, values):
        """Calculate trend using linear regression."""
        if len(values) < 2:
            return 0
        
        x = list(range(len(values)))
        n = len(values)
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return round(slope, 3)
    
    def generate_pdf(self, data, user, start_date, end_date):
        """Generate detailed PDF report using reportlab."""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from io import BytesIO
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.darkblue,
            borderPadding=5
        )
        
        subheading_style = ParagraphStyle(
            'SubHeading',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.darkgreen
        )
        
        # Build content
        story = []
        
        # Title Page
        story.append(Paragraph("Mental Health Journal Report", title_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"<b>Patient:</b> {user.first_name} {user.last_name}", styles['Normal']))
        story.append(Paragraph(f"<b>Email:</b> {user.email}", styles['Normal']))
        story.append(Paragraph(f"<b>Report Period:</b> {start_date} to {end_date}", styles['Normal']))
        story.append(Paragraph(f"<b>Generated:</b> {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        summary_text = f"""
        This comprehensive mental health report covers {data['summary']['days_tracked']} days of tracking with {data['summary']['total_entries']} journal entries.
        The analysis reveals key patterns in mood, stress, sleep, and daily activities that provide valuable insights into mental well-being.
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Key Statistics Table
        story.append(Paragraph("Key Statistics", subheading_style))
        summary_data = [
            ['Metric', 'Value', 'Details'],
            ['Total Entries', str(data['summary']['total_entries']), f"Over {data['summary']['days_tracked']} days"],
            ['Average Mood', f"{data['mood']['average']:.1f}/10", f"Range: {data['mood']['lowest']}-{data['mood']['highest']}"],
            ['Mood Trend', f"{data['mood']['trend']:+.2f}", 'Positive = improving, Negative = declining'],
        ]
        
        if 'stress' in data and data['stress']:
            summary_data.append(['Average Stress', f"{data['stress']['average']:.1f}/10", f"Range: {data['stress']['lowest']}-{data['stress']['highest']}"])
        
        if 'sleep' in data and data['sleep']:
            summary_data.append(['Average Sleep', f"{data['sleep']['average']:.1f} hours", f"Best: {data['sleep']['best']:.1f}h, Worst: {data['sleep']['worst']:.1f}h"])
        
        summary_table = Table(summary_data, colWidths=[1.5*inch, 1*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Mood Analysis
        story.append(Paragraph("Detailed Mood Analysis", heading_style))
        mood_text = f"""
        <b>Average Mood Score:</b> {data['mood']['average']:.1f}/10<br/>
        <b>Mood Range:</b> {data['mood']['lowest']} to {data['mood']['highest']}<br/>
        <b>Trend Analysis:</b> {'Positive improvement' if data['mood']['trend'] > 0.1 else 'Negative decline' if data['mood']['trend'] < -0.1 else 'Stable pattern'}<br/>
        <b>Consistency:</b> {data['mood'].get('consistency', 'N/A')}% mood stability
        """
        story.append(Paragraph(mood_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Mood interpretation
        if data['mood']['average'] >= 7:
            mood_interpretation = "Your mood scores indicate generally positive mental well-being during this period."
        elif data['mood']['average'] >= 5:
            mood_interpretation = "Your mood scores show moderate well-being with room for improvement."
        else:
            mood_interpretation = "Your mood scores suggest challenges that may benefit from professional support."
        
        story.append(Paragraph(f"<b>Interpretation:</b> {mood_interpretation}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Stress Analysis
        if 'stress' in data and data['stress']:
            story.append(Paragraph("Stress Analysis", heading_style))
            stress_text = f"""
            <b>Average Stress Level:</b> {data['stress']['average']:.1f}/10<br/>
            <b>Stress Range:</b> {data['stress']['lowest']} to {data['stress']['highest']}<br/>
            <b>Stress Trend:</b> {'Increasing' if data['stress'].get('trend', 0) > 0 else 'Decreasing' if data['stress'].get('trend', 0) < 0 else 'Stable'}
            """
            story.append(Paragraph(stress_text, styles['Normal']))
            
            if data['stress']['average'] > 7:
                stress_advice = "High stress levels detected. Consider stress management techniques, relaxation exercises, or professional support."
            elif data['stress']['average'] < 4:
                stress_advice = "Excellent stress management! You're maintaining healthy stress levels."
            else:
                stress_advice = "Moderate stress levels. Continue monitoring and consider stress reduction strategies."
            
            story.append(Paragraph(f"<b>Recommendation:</b> {stress_advice}", styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Sleep Analysis
        if 'sleep' in data and data['sleep']:
            story.append(Paragraph("Sleep Analysis", heading_style))
            sleep_text = f"""
            <b>Average Sleep Duration:</b> {data['sleep']['average']:.1f} hours per night<br/>
            <b>Best Night:</b> {data['sleep']['best']:.1f} hours<br/>
            <b>Worst Night:</b> {data['sleep']['worst']:.1f} hours<br/>
            <b>Sleep Consistency:</b> {data['sleep']['consistency']}%
            """
            story.append(Paragraph(sleep_text, styles['Normal']))
            
            if data['sleep']['average'] < 7:
                sleep_advice = "Insufficient sleep detected. Aim for 7-9 hours nightly for optimal mental health."
            elif data['sleep']['average'] > 9:
                sleep_advice = "Adequate sleep duration. Ensure quality sleep with good sleep hygiene."
            else:
                sleep_advice = "Good sleep duration. Maintain consistent sleep schedule for mental well-being."
            
            story.append(Paragraph(f"<b>Recommendation:</b> {sleep_advice}", styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Activities Analysis
        if 'activities' in data and data['activities']:
            story.append(Paragraph("Activity Patterns", heading_style))
            story.append(Paragraph("Most frequently logged activities during this period:", styles['Normal']))
            
            activity_data = [['Activity', 'Frequency', 'Percentage']]
            total_activities = sum(activity[1] for activity in data['activities'])
            for activity in data['activities'][:10]:  # Top 10 activities
                percentage = (activity[1] / total_activities) * 100
                activity_data.append([activity[0], str(activity[1]), f"{percentage:.1f}%"])
            
            activity_table = Table(activity_data, colWidths=[2*inch, 1*inch, 1*inch])
            activity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(activity_table)
            story.append(Spacer(1, 20))
        
        # Emotions Analysis
        if 'emotions' in data and data['emotions']:
            story.append(Paragraph("Emotional Patterns", heading_style))
            story.append(Paragraph("Most frequently experienced emotions during this period:", styles['Normal']))
            
            emotion_data = [['Emotion', 'Frequency', 'Percentage']]
            total_emotions = sum(emotion[1] for emotion in data['emotions'])
            for emotion in data['emotions'][:10]:  # Top 10 emotions
                percentage = (emotion[1] / total_emotions) * 100
                emotion_data.append([emotion[0], str(emotion[1]), f"{percentage:.1f}%"])
            
            emotion_table = Table(emotion_data, colWidths=[2*inch, 1*inch, 1*inch])
            emotion_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(emotion_table)
            story.append(Spacer(1, 20))
        
        # Insights and Recommendations
        story.append(PageBreak())
        story.append(Paragraph("Insights & Recommendations", heading_style))
        
        # Generate insights
        insights = []
        
        # Mood insights
        if data['mood']['trend'] > 0.1:
            insights.append("Your mood has been improving over time - great progress!")
        elif data['mood']['trend'] < -0.1:
            insights.append("Your mood has been declining - consider reaching out for support.")
        
        if data['mood']['average'] < 5:
            insights.append("Low average mood scores suggest you may benefit from professional mental health support.")
        
        # Stress insights
        if 'stress' in data and data['stress']:
            if data['stress']['average'] > 7:
                insights.append("High stress levels detected - consider stress management techniques like meditation or exercise.")
            elif data['stress']['average'] < 4:
                insights.append("Excellent stress management - you're maintaining healthy stress levels.")
        
        # Sleep insights
        if 'sleep' in data and data['sleep']:
            if data['sleep']['average'] < 7:
                insights.append("Insufficient sleep may be impacting your mental health - aim for 7-9 hours nightly.")
            elif data['sleep']['consistency'] < 70:
                insights.append("Inconsistent sleep patterns detected - try to maintain a regular sleep schedule.")
        
        # Activity insights
        if 'activities' in data and data['activities']:
            top_activity = data['activities'][0][0] if data['activities'] else None
            if top_activity:
                insights.append(f"'{top_activity}' is your most common activity - consider how it affects your mood.")
        
        # Add insights to PDF
        for i, insight in enumerate(insights, 1):
            story.append(Paragraph(f"<b>{i}.</b> {insight}", styles['Normal']))
            story.append(Spacer(1, 8))
        
        # General recommendations
        story.append(Paragraph("General Recommendations", subheading_style))
        recommendations = [
            "Continue tracking your mood and activities regularly for better insights",
            "Consider establishing a consistent daily routine for better mental health",
            "Practice mindfulness or meditation to improve emotional awareness",
            "Maintain regular sleep schedule and aim for 7-9 hours nightly",
            "Engage in physical activities that you enjoy",
            "Don't hesitate to seek professional help if you're struggling"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"• {rec}", styles['Normal']))
            story.append(Spacer(1, 4))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("--- End of Report ---", styles['Normal']))
        story.append(Paragraph(f"Generated by Mental Health Journal on {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer


class SharedReportView(View):
    """View shared report (no login required)."""
    
    def get(self, request, token):
        """Display shared report."""
        report = get_object_or_404(Report, share_token=token)
        
        # Check if share has expired
        if report.is_share_expired:
            return render(request, 'reports/expired.html')
        
        # Log access
        ReportAccess.objects.create(
            report=report,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        context = {
            'report': report,
            'data': report.data,
            'is_shared': True,
            'report_id': report.id,
        }
        return render(request, 'reports/shared_report.html', context)


class DownloadReportView(LoginRequiredMixin, View):
    """Download report PDF (requires login)."""
    
    def get(self, request, report_id):
        """Download report PDF."""
        report = get_object_or_404(Report, id=report_id, user=request.user)
        
        if not report.pdf_file:
            return JsonResponse({'error': 'PDF not available'}, status=404)
        
        response = HttpResponse(report.pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
        return response


class DownloadSharedReportView(View):
    """Download shared report PDF (no login required)."""
    
    def get(self, request, token):
        """Download shared report PDF."""
        report = get_object_or_404(Report, share_token=token)
        
        # Check if share has expired
        if report.is_share_expired:
            return JsonResponse({'error': 'Share link has expired'}, status=410)
        
        if not report.pdf_file:
            return JsonResponse({'error': 'PDF not available'}, status=404)
        
        # Log access
        ReportAccess.objects.create(
            report=report,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        response = HttpResponse(report.pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
        return response
