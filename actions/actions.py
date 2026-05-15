from typing import Any, Text, Dict, List

import re

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.types import DomainDict


class ValidateInterviewForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_interview_form"

    async def validate_experience(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        text = str(slot_value).lower().strip()

        if "нет опыта" in text or "без опыта" in text:
            return {
                "experience": slot_value,
                "experience_years": 0.0,
            }

        match = re.search(r"(\d+(?:\.\d+)?)", text)

        if not match:
            dispatcher.utter_message(
                text="Не удалось определить ваш опыт. Пожалуйста, укажите количество лет или напишите 'нет опыта'."
            )
            return {"experience": None}

        years = float(match.group(1))

        if 0 <= years <= 70:
            return {
                "experience": slot_value,
                "experience_years": years,
            }

        dispatcher.utter_message(
            text="Пожалуйста, укажите корректное количество лет опыта."
        )
        return {"experience": None}

    async def validate_salary(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        text = str(slot_value).lower().strip()

        if not text:
            dispatcher.utter_message(
                text="Пожалуйста, укажите зарплатные ожидания."
            )
            return {"salary": None}

        cleaned = (
            text.replace(" ", "")
            .replace(",", ".")
            .replace("рублей", "")
            .replace("руб", "")
            .replace("₽", "")
        )

        numbers = re.findall(r"\d+(?:\.\d+)?", cleaned)

        if not numbers:
            dispatcher.utter_message(
                text="Не удалось определить зарплату. Напишите, например: 200000, 200к или 200 тысяч."
            )
            return {"salary": None}

        salary = float(numbers[0])

        if "к" in cleaned or "тыс" in cleaned:
            salary *= 1000

        if salary < 1000:
            salary *= 1000

        if salary < 10000 or salary > 2000000:
            dispatcher.utter_message(
                text="Пожалуйста, укажите реалистичную зарплату, например: 150000 или 200к."
            )
            return {"salary": None}

        return {"salary": str(int(salary))}


class ActionAskSoftSkills(Action):
    def name(self) -> Text:
        return "action_ask_soft_skills"

    ROLE_KEYWORDS: Dict[str, Dict[str, int]] = {
        "Data Engineer": {
            "etl": 3,
            "pipeline": 3,
            "data pipeline": 3,
            "airflow": 3,
            "kafka": 3,
            "spark": 3,
            "hadoop": 3,
            "dbt": 2,
            "dataflow": 2,
            "sql": 2,
            "nosql": 2,
            "mongodb": 2,
            "postgresql": 2,
            "data lake": 2,
            "data warehouse": 2,
            "data integration": 2,
            "presto": 2,
            "hive": 2,
            "flink": 2,
            "обработка данных": 2,
            "трансформация данных": 2,
        },
        "MLOps Engineer": {
            "mlops": 3,
            "ci/cd": 3,
            "kubernetes": 3,
            "docker": 3,
            "деплой": 3,
            "мониторинг": 2,
            "логи": 2,
            "prometheus": 2,
            "grafana": 2,
            "mlflow": 3,
            "kubeflow": 3,
            "gitlab ci": 2,
            "github actions": 2,
            "jenkins": 2,
            "terraform": 2,
            "helm": 2,
            "автоматизация": 2,
            "scaling": 2,
        },
        "Data Scientist": {
            "машинное обучение": 3,
            "ml": 3,
            "deep learning": 3,
            "нейросети": 3,
            "scikit-learn": 3,
            "sklearn": 3,
            "tensorflow": 3,
            "pytorch": 3,
            "xgboost": 2,
            "catboost": 2,
            "lightgbm": 2,
            "pandas": 2,
            "numpy": 2,
            "statistics": 2,
            "статистика": 2,
            "random forest": 2,
            "градиентный бустинг": 2,
            "nlp": 2,
            "computer vision": 2,
            "cv": 2,
            "a/b test": 2,
            "ab test": 2,
        },
        "Data Analyst": {
            "анализ данных": 3,
            "визуализация": 3,
            "дашборд": 3,
            "tableau": 3,
            "power bi": 3,
            "looker": 2,
            "sql": 2,
            "excel": 2,
            "matplotlib": 2,
            "seaborn": 2,
            "статистика": 2,
            "a/b test": 2,
            "ab test": 2,
            "отчет": 2,
            "dashboard": 2,
            "бизнес-требования": 2,
            "продуктовые метрики": 2,
        },
        "Project Manager": {
            "управление проектами": 3,
            "project management": 3,
            "agile": 3,
            "scrum": 3,
            "kanban": 3,
            "jira": 2,
            "trello": 2,
            "управление командой": 2,
            "team management": 2,
            "коммуникация": 2,
            "stakeholder": 2,
            "бюджет": 2,
            "риски": 2,
            "roadmap": 2,
            "ведение проектов": 2,
        },
    }

    CONFIDENCE_THRESHOLD = 4

    def _calculate_score(self, text: str, role_keywords: Dict[str, int]) -> int:
        if not text:
            return 0

        text_lower = text.lower()
        score = 0

        for keyword, weight in role_keywords.items():
            if keyword in text_lower:
                score += weight

        return score

    def _compute_role_scores(
        self,
        education: str,
        experience: str,
        hard_skills: str,
        projects: str,
    ) -> Dict[str, int]:

        combined_text = f"{education} {experience} {hard_skills} {projects}"

        scores = {}
        for role, keywords in self.ROLE_KEYWORDS.items():
            scores[role] = self._calculate_score(combined_text, keywords)

        return scores

    def _adjust_by_experience(
        self,
        scores: Dict[str, int],
        experience_years: float,
    ) -> Dict[str, int]:

        if experience_years < 1:
            scores["Project Manager"] -= 2
            scores["MLOps Engineer"] -= 1

        elif experience_years >= 3:
            scores["Project Manager"] += 1
            scores["Data Scientist"] += 1

        return scores

    def determine_likely_role(
        self,
        education: str,
        experience: str,
        hard_skills: str,
        projects: str,
        experience_years: float,
    ) -> str | None:

        scores = self._compute_role_scores(
            str(education or ""),
            str(experience or ""),
            str(hard_skills or ""),
            str(projects or ""),
        )

        scores = self._adjust_by_experience(scores, experience_years)

        best_role = max(scores, key=scores.get)
        best_score = scores[best_role]

        if best_score < self.CONFIDENCE_THRESHOLD:
            return None

        return best_role

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        education = tracker.get_slot("education") or ""
        experience = tracker.get_slot("experience") or ""
        hard_skills = tracker.get_slot("hard_skills") or ""
        projects = tracker.get_slot("projects") or ""
        experience_years = tracker.get_slot("experience_years") or 0.0

        likely_role = self.determine_likely_role(
            education=education,
            experience=experience,
            hard_skills=hard_skills,
            projects=projects,
            experience_years=experience_years,
        )

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

        return [SlotSet("likely_role", likely_role)]


class ActionSetSoftSkills(Action):
    def name(self) -> Text:
        return "action_set_soft_skills"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        text = tracker.latest_message.get("text", "")
        return [SlotSet("soft_skills", text)]


class ActionEvaluateCandidate(Action):
    def name(self) -> Text:
        return "action_evaluate_candidate"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        likely_role = tracker.get_slot("likely_role")
        desired_role = tracker.get_slot("desired_role")

        if likely_role is None:
            dispatcher.utter_message(response="utter_no_match")
            return []

        if desired_role is None:
            dispatcher.utter_message(response="utter_no_match")
            return []

        if likely_role.lower() in str(desired_role).lower():
            explanation = "Ваш профиль отлично соответствует этой позиции."
        else:
            explanation = (
                "Хотя вы рассматривали другую позицию, "
                "ваш опыт и навыки лучше подходят для этой роли."
            )

        dispatcher.utter_message(
            response="utter_offer_role",
            role=likely_role,
            explanation=explanation,
        )

        return []