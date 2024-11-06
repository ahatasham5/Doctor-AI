from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import openai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os

# Global variable to accumulate conversation text for documentation
conversation_log = ""

class ActionProvideGeneralHealthInfo(Action):
    def name(self) -> Text:
        return "action_provide_general_health_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global conversation_log

        health_issue = tracker.get_slot("health_issue")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Provide general health information about {health_issue}."}],
            max_tokens=100
        )
        health_info = response.choices[0].message['content'].strip()
        dispatcher.utter_message(text=health_info)

        # Log the conversation details for documentation
        conversation_log += f"User health issue: {health_issue}\nHealth Information: {health_info}\n\n"

        return [] 

class ActionProvideGeneralHealthInfo(Action):
    def name(self) -> Text:
        return "action_provide_health_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global conversation_log

        health_issue = tracker.get_slot("health_issue")  # Retrieve the initial health issue
        follow_up_answer = tracker.get_slot("follow_up_answer")  # Retrieve the follow-up answer
        
        # Combine health issue and follow-up answer if both are provided
        if health_issue and follow_up_answer:
            combined_health_issue = f"{health_issue}. {follow_up_answer}"
        else:
            combined_health_issue = health_issue or follow_up_answer  # Use whichever is available

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Provide general health information about {combined_health_issue}."}],
            max_tokens=100
        )
        health_info = response.choices[0].message['content'].strip()
        dispatcher.utter_message(text=health_info)

        # Log the conversation details for documentation
        conversation_log += f"User health issue: {combined_health_issue}\nHealth Information: {health_info}\n\n"

        return []


class ActionFollowUpQuestion(Action):
    def name(self) -> Text:
        return "action_follow_up_question"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global conversation_log
        
        follow_up_answer = tracker.get_slot("health_issue")
        problem_understood = False  # Initialize the variable

        # Check if enough information has been provided
        if follow_up_answer and ("pain" in follow_up_answer.lower() or "duration" in follow_up_answer.lower()):
            problem_understood = True
            conversation_log += f"Follow-up answer: {follow_up_answer}\n"
        
        return [
            SlotSet("problem_understood", problem_understood)  # Use the correct slot name
        ]


class ActionFollowUpAnswer(Action):
    def name(self) -> Text:
        return "action_follow_up_answer"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global conversation_log
        
        follow_up_answer = tracker.get_slot("follow_up_answer")
        problem_understood = False  # Initialize the variable

        # Check if enough information has been provided
        if follow_up_answer and ("pain" in follow_up_answer.lower() or "duration" in follow_up_answer.lower()):
            problem_understood = True
            conversation_log += f"Follow-up answer: {follow_up_answer}\n"

        return [
            SlotSet("problem_understood", problem_understood)  # Use the correct slot name
        ]


class ActionRecommendDoctor(Action):
    def name(self) -> Text:
        return "action_recommend_doctor"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global conversation_log
        
        health_issue = tracker.get_slot("health_issue")
        doctor = "Dr. Smith"
        dispatcher.utter_message(text=f"Based on your issue, I recommend seeing {doctor}.")

        # Log doctor recommendation
        conversation_log += f"Doctor recommendation for {health_issue}: {doctor}\n\n"

        return [SlotSet("selected_doctor", doctor)]

class ActionBookAppointment(Action):
    def name(self) -> Text:
        return "action_book_appointment"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global conversation_log

        booking_successful = True
        if booking_successful:
            dispatcher.utter_message(text="Your appointment has been booked.")
            conversation_log += "Appointment booking: Successful\n\n"
            return [SlotSet("booking_successful", True)]
        else:
            dispatcher.utter_message(text="Failed to book the appointment.")
            conversation_log += "Appointment booking: Failed\n\n"
            return [SlotSet("booking_successful", False)]

class ActionGeneratePdf(Action):
    def name(self) -> Text:
        return "action_generate_pdf"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global conversation_log

        # Generate summaries for the patient problem and chatbot response using the model
        patient_summary = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Summarize only the patient's health issue: {conversation_log}"}],
            max_tokens=100
        ).choices[0].message['content'].strip()

        bot_summary = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Summarize the response of only chatbot, based on the following medical instruction from chatbot: {conversation_log}"}],
            max_tokens=100
        ).choices[0].message['content'].strip()

        # Generate recommendation for the patient
        bot_recommendation = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Based on the conversation, suggest only recommended steps and medicine for the patient? {conversation_log}"}],
            max_tokens=100
        ).choices[0].message['content'].strip()

        # Set output directory and ensure it exists
        output_dir = "C:/Users/KHAN GADGET/Documents/my_chatbot_outputs"
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, "conversation_summary.pdf")

        # Logo path
        logo_path = "C:/Users/KHAN GADGET/Documents/ewu.png"

        # Create PDF document
        pdf_doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        elements = []

        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title", fontSize=18, alignment=1, leading=20, spaceAfter=20, textColor=colors.darkblue)
        bold_style = ParagraphStyle("Bold", fontSize=12, leading=14, spaceAfter=10, textColor=colors.black, leftIndent=20, fontName="Helvetica-Bold")
        content_style = ParagraphStyle("Content", fontSize=12, leading=14, textColor=colors.black, leftIndent=20)
        light_style = ParagraphStyle("Light", fontSize=11, leading=14, textColor=colors.gray, leftIndent=20)

        # Add logo
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=1.5 * inch, height=1 * inch)
            logo.hAlign = 'LEFT'
            elements.append(logo)

        # Add title
        title = Paragraph("Medical Summary", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Patient Problem Summary Section
        elements.append(Paragraph("Patient Problem Description:", bold_style))
        elements.append(Paragraph(patient_summary, content_style))
        elements.append(Spacer(1, 12))

        # Chatbot Response Summary Section
        elements.append(Paragraph("Chatbot Response:", bold_style))
        elements.append(Paragraph(bot_summary, content_style))
        elements.append(Spacer(1, 12))

        # Bot Recommendation Section
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Recommended Next Steps:", bold_style))
        elements.append(Paragraph(bot_recommendation, content_style))

        # Detailed Conversation Log
        elements.append(Paragraph("Conversation History", bold_style))
        for line in conversation_log.split("\n"):
            if line.startswith("Patient:"):
                elements.append(Paragraph("<b>Patient:</b> " + line[8:], light_style))
            elif line.startswith("Chatbot:"):
                elements.append(Paragraph("<b>Chatbot:</b> " + line[8:], light_style))
            else:
                elements.append(Paragraph(line, light_style))

        # Build PDF
        pdf_doc.build(elements)

        # Provide the link to download the PDF
        pdf_url = f"http://localhost:5005/static/conversation_summary.pdf"
        dispatcher.utter_message(response="utter_pdf_ready", pdf_url=pdf_url)

        # Clear the log after generating the PDF
        conversation_log = ""

        return []