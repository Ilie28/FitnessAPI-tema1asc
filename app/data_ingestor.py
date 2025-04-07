"""Modul pentru citirea și procesarea datelor despre fitness dintr-un fișier CSV."""
import pandas as pd

class DataIngestor:
    """Clasa care citește fișierul CSV și oferă metode de agregare a datelor."""
    def __init__(self, csv_path: str):
        """Inițializează citirea datelor din fișierul CSV."""
        self.df = pd.read_csv(csv_path)

        self.questions_best_is_min = [
            'Percent of adults aged 18 years and older who have an overweight classification',
            'Percent of adults aged 18 years and older who have obesity',
            'Percent of adults who engage in no leisure-time physical activity',
            'Percent of adults who report consuming fruit less than one time daily',
            'Percent of adults who report consuming vegetables less than one time daily'
        ]

        self.questions_best_is_max = [
            ('Percent of adults who achieve at least 150 minutes a week of moderate-intensity '
            'aerobic physical activity or 75 minutes a week of vigorous-intensity aerobic '
            'activity (or an equivalent combination)'),
            ('Percent of adults who achieve at least 150 minutes a week of moderate-intensity '
            'aerobic physical activity or 75 minutes a week of vigorous-intensity aerobic '
            'physical activity and engage in muscle-strengthening activities on 2 or '
            'more days a week'),
            ('Percent of adults who achieve at least 300 minutes a week of moderate-intensity '
            'aerobic physical activity or 150 minutes a week of vigorous-intensity '
            'aerobic activity (or an equivalent combination)'),
            ('Percent of adults who engage in muscle-strengthening activities on 2 or '
            'more days a week'),
        ]
    def filter_by_question(self, question):
        """Returnează rândurile din DataFrame pentru o întrebare anume."""
        return self.df[self.df['Question'] == question]

    def get_states_mean(self, question):
        """Returnează media pe state pentru o întrebare anume."""
        df = self.filter_by_question(question)
        return df.groupby('LocationDesc')['Data_Value'].mean().sort_values().to_dict()

    def get_state_mean(self, question, state):
        """Returnează media pentru o întrebare anume și un stat specific."""
        df = self.filter_by_question(question)
        return df[df['LocationDesc'] == state]['Data_Value'].mean()

    def get_global_mean(self, question):
        """Returnează media globală pentru o întrebare anume."""
        df = self.filter_by_question(question)
        return df['Data_Value'].mean()

    def get_mean_by_category(self, question, state=None):
        """Returnează media pe categorii de stratificare pentru o întrebare anume."""
        df = self.filter_by_question(question)
        if state:
            df = df[df['LocationDesc'] == state]
        return (
            df.groupby(['StratificationCategory1', 'Stratification1'])['Data_Value']
            .mean()
            .to_dict()
        )
