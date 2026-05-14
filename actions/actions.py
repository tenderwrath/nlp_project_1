from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

class ActionAskSoftSkills(Action):
    def name(self) -> Text:
        return "action_ask_soft_skills"
    
    def determine_likely_role(self, education, experience, hard_skills, projects):
        edu = education.lower() if education else ""
        exp = experience.lower() if experience else ""
        hard = hard_skills.lower() if hard_skills else ""
        proj = projects.lower() if projects else ""

        if any(word in hard + " " + exp + " " + proj for word in ["pipeline", "etl", "airflow", "kafka", "spark", "datalake", "sql", "nosql"]):
            return "Data Engineer"

        if any(word in hard + " " + exp + " " + proj for word in ["mlops", "kubernetes", "docker", "ci/cd", "деплой", "мониторинг", "логи", "gitlab ci", "github actions"]):
            return "MLOps Engineer"

        if any(word in hard + " " + exp + " " + proj for word in ["scikit-learn", "sklearn", "tensorflow", "pytorch", "xgboost", "catboost", "нейросети", "deep learning", "random forest", "pandas", "numpy", "машинное обучение"]):
            return "Data Scientist"

        if any(word in hard + " " + exp + " " + proj for word in ["анализ данных", "статистика", "excel", "tableau", "power bi", "matplotlib", "seaborn", "sql", "визуализация", "дашборд"]):
            return "Data Analyst"

        if any(word in hard + " " + exp + " " + proj for word in ["agile", "scrum", "kanban", "jira", "управление проектами", "управление командой", "бюджет", "коммуникация", "stakeholder"]):
            return "Project Manager"

        return None

    def run(self, dispatcher, tracker, domain):
        education = tracker.get_slot("education") or ""
        experience = tracker.get_slot("experience") or ""
        hard_skills = tracker.get_slot("hard_skills") or ""
        projects = tracker.get_slot("projects") or ""

        likely_role = self.determine_likely_role(education, experience, hard_skills, projects)
        events = [SlotSet("likely_role", likely_role)]

        dispatcher.utter_message(response="utter_ask_soft_skills")

        if likely_role == "Project Manager":
            dispatcher.utter_message(response="utter_ask_soft_skills_pm")
        elif likely_role == "Data Analyst":
            dispatcher.utter_message(response="utter_ask_soft_skills_da")
        elif likely_role == "Data Engineer":
            dispatcher.utter_message(response="utter_ask_soft_skills_de")
        elif likely_role == "Data Scientist":
            dispatcher.utter_message(response="utter_ask_soft_skills_ds")
        elif likely_role == "MLOps Engineer":
            dispatcher.utter_message(response="utter_ask_soft_skills_mlops")
        else:
            dispatcher.utter_message(response="utter_ask_soft_skills")

        return events

class ActionSetSoftSkills(Action):
    def name(self) -> Text:
        return "action_set_soft_skills"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = tracker.latest_message.get('text', '')
        return [SlotSet("soft_skills", text)]

class ActionEvaluateCandidate(Action):
    def name(self) -> Text:
        return "action_evaluate_candidate"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        likely_role = tracker.get_slot("likely_role")
        desired_role = tracker.get_slot("desired_role")

        if likely_role is None:
            dispatcher.utter_message(response="utter_no_match")
            return []

        if likely_role == desired_role:
            explanation = "Ваш профиль отлично соответствует этой позиции."
        else:
            explanation = ("Хотя вы рассматривали другую позицию, "
                           "ваш опыт и навыки лучше подходят для этой роли.")

        dispatcher.utter_message(
            response="utter_offer_role",
            role=likely_role,
            explanation=explanation
        )
        return []