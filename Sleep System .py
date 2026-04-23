 #Keenan Ray
#01/09/2025
#Sleep System OOP project

#Circadian Rhythm Class

"""
Sleep/Circadian System - v1.0

Purpose:
Based on cortisol timing, determine whether behaviors align according to physiological
guidelines.

Non - goals:
 - Does not optimize behavior
 - Does not coach or motivate
 - Does not make decisions
 - Does not track streaks or scores

 This tool serves as truth for circadian alignment.

 I built a rule-based system that checks if a coritisol spike occurred early
 in the day, tracks specific circdian rhythm behaviors, and assess what stabilizes
 sleep and energy
 """


SEVERITY_RANK = {
"high": 3,
"medium": 2,
"low": 1
}

import json

def load_last_day(today_date):
    try:
        with open("log.json", "r") as f:
            lines = f.readlines()

        # walk backwards through the log
        for line in reversed(lines):
            entry = json.loads(line)
            if entry["date"] != today_date:
                return entry

    except FileNotFoundError:
        pass

    return None


    
def compute_delta(today, yesterday):
    if not yesterday:
        return ["No prior day to compare against"]

    def caffeine_value(x):
        # supports either an int (200) or a list like [(200, 7.5), (100, 13.0)]
        if isinstance(x, list):
            return sum(mg for mg, _ in x)
        return x

    deltas = []

    score_change = today["performance_score"] - yesterday["performance_score"]
    if abs(score_change) >= 0.5:
        direction = "increased" if score_change > 0 else "decreased"
        deltas.append(f"Performance score {direction} by {round(score_change, 1)}")

    if today["focus_minutes"] != yesterday["focus_minutes"]:
        delta = today["focus_minutes"] - yesterday["focus_minutes"]
        deltas.append(f"Focus changed by {delta} min")

    today_caf = caffeine_value(today["caffeine"])
    yest_caf = caffeine_value(yesterday["caffeine"])
    if today_caf != yest_caf:
        delta = today_caf - yest_caf
        deltas.append(f"Caffeine changed by {delta} mg")

    return deltas


class CircadianRhythm:
    #this is the initializor for the specific phase of circadian rhythm
    def __init__(self, phase):
        self.phase = phase
        self.shift = 0 #negative is earlier while positive is later



    def apply_light(self, hour, minutes = 30):
        if 6 <= hour <= 10: #morning light, subtracts minutes, so that shift becomes more negative  #pushes earlier (in between 6 am and 10 am)
            self.shift -= minutes
        elif 20 <= hour <= 24: #night light between 8 pm and midnight, adds minutes, shift becomes more positive
                                #pushes you later
            self.shift += minutes
    def status(self):
        if self.shift <= -60:
            return "advanced" #less than 60 mins = how strong (or weak) the shift is
        elif self.shift >= 60:
            return "delayed" 
        else:
            return "aligned"

    def shift(self, light_exposure):
        if light_exposure == 'morning':
            self.__phase = "earlier"
        elif light_exposure == 'night':
            self.__phase == 'later'

    def __str__(self):
        return f"Circadian phase: {self.phase}"

#Sleep Session
class SleepSession:
    def __init__(self, start_time, end_time, quality):
        self.start_time = start_time
        self.end_time = end_time
        self.quality = quality

    def get_duration(self):
        #In the case of 10 pm start to 7 am end, the start is greater than the end
        #so it will be 24 - (10 + 12 = 22) = 2 hours
        #then it will be midnight -> 7 am which  = 7 hours
        #then the math is 2+7 = 9 hours
        #24-22 = 2 + 7 = 9 hours
        if self.end_time >= self.start_time:
            return self.end_time - self.start_time
        else:
            return (24 - self.start_time) + self.end_time
#class Person
class Person:
    def __init__(self, name, circadian):
        self.name = name
        self.circadian = circadian
        self.energy = 50  #energy is from 0-100
        self.sleep_need = 8
        self.sleep_debt = 0
        self.caffeine_level = 0 #tracking these in mg
        self.training_load = 0
        self.recovery = 100
        self.base_energy = 50
        self.energy = self.base_energy
        self.recovery = 100

    def do_training(self, intensity):
        #intensity: 1 is light, 2 is moderate, 3 is hard
        self.training_load += intensity * 10 #harder training = more fatigue, means that recovery gets used up
        self.recovery -= intensity * 8 
        #This function calls the duration of the sleep session as the hours, then subtracts the hours from
        #the sleep need
        #if you sleep more, energy increases, debt decreases
        #if you sleep less, energy decreases, debt increases
    def drink_caffeine(self, mg, hour):
        self.caffeine_level += mg
        self.energy += mg * 0.05 #how much boost user gets

        if hour >= 14:
            self.sleep_debt += mg/100
            self.circadian.shift += mg/50

    def metabolize_caffeine(self):
        self.caffeine_level *= 0.5 #half life per day

    def get_circadian_status(self):
        return self.circadian.status()
    def apply_sleep(self, session):
        hours = session.get_duration()

        # reset for the day
        self.energy = self.base_energy

        # sleep debt
        delta = hours - self.sleep_need
        self.sleep_debt -= delta

        # energy from sleep
        self.energy += hours * 5

        # recovery from sleep
        self.recovery += hours * 5
        self.recovery = min(self.recovery, 100)

        # fatigue limits energy
        self.energy *= (self.recovery / 100)

    def sleep(self, sleep_session):
        #the energy is the sleep_hours * 10
        self.energy += sleep_session.get_duration() * 10
        if self.energy > 100:
            self.energy = 100
#sleep Manager class
class SleepManager:
    def __init__(self, person):
        self.person = person #person object
        self.sessions = [] #empty list for each instance to be passed.
                           #stores the objects 
    def log_sleep(self, session):
        self.sessions.append(session)
        self.person.apply_sleep(session)
    def run_day(self, day):
        day.person = self.person
        self.person.day = day
        self.person.current_day = day.date
        if day.sleep:
            self.log_sleep(day.sleep)

        for mg, hour in day.caffeine:
            self.person.drink_caffeine(mg, hour)

        for hour, minutes in day.light:
            self.person.circadian.apply_light(hour, minutes)

        self.person.do_training(day.training)

        # stress hurts recovery
        self.person.recovery -= self.person.day.stress * 5

        # screens delay circadian clock
        self.person.circadian.shift += self.person.day.screen_minutes * 0.05
        self.person.energy = max(0, min(self.person.energy, 100))
        
        day.evaluate_cortisol()

        
        '''
    def explain_delta(self, last):
        contributors = []

        if not last:
            return ["No prior day to compare against"]

        if self.person.energy > last["energy"]:
            explanations.append("Energy increased due to improved sleep consistency")

        if self.person.day.focus_minutes > last["focus_minutes"]:
            explanations.append("Focus improved with additional deep work time")

        if self.person.caffeine < last["caffeine"]:
            explanations.append("Lower caffeine likely improved sleep pressure")

        return explanations
        '''

    def todays_priority(self, last_day=None):
        recs = self.person.day.recommendation()
        if not recs:
            return "Priority: Maintain current routine"

        action, reason, category, severity = recs[0]

        if last_day:
            delta = compute_delta(
                {
                    "performance_score": self.performance_score(self.person.day),
                    "focus_minutes": self.person.day.focus_minutes,
                    "caffeine": self.person.day.total_caffeine()
                },
                last_day
            )
            if delta:
                return f"Priority: {action} — because {delta[0]}"

        return f"Priority: {action}"


    def performance_score(self, day):
        score = 0
        #energy contributes up to 40 points
        score += self.person.energy * 0.4
        #Focus contributes up to 30 points (cap at 180 min)
        score += min(day.focus_minutes, 180) / 180 * 30
        #Stress substracts up to 20 points
        score -= day.stress
        #Screens subtract up to 10 points
        score -= min(day.screen_minutes, 120) / 120 * 10
        return max(0, round(score,1))
        
 

    def save_day(self, day):
        import json
        data = {
            "date": day.date,
            "sleep_start": day.sleep.start_time,
            "sleep_end": day.sleep.end_time,
            "training": day.training,
            "caffeine": day.total_caffeine(),        # numeric mg for easy comparisons
            "caffeine_events": day.caffeine,         # keep the raw events too
            "light": day.light,
            "focus_minutes": day.focus_minutes,
            "energy": self.person.energy,
            "recovery": self.person.recovery,
            "sleep_debt": self.person.sleep_debt,
            "circadian_shift": self.person.circadian.shift,
            "performance_score": self.performance_score(day),
            "cortisol_spike": self.person.day.cortisol.spike_achieved,
            "late_activation": self.person.day.cortisol.late_activation,

        }

        with open("log.json", "a") as f:
            f.write(json.dumps(data) + "\n")

        
    def render_summary(self):
        print(self.person.name)
        print("Date:", self.person.day.date)
        print("Energy:", self.person.energy)
        print("Recovery:", round(self.person.recovery, 1))
        print("Sleep debt:", self.person.sleep_debt)
        print("Circadian:", self.person.get_circadian_status())
        print("Shift (min):", self.person.circadian.shift)
        print("Caffeine:", round(self.person.caffeine_level, 1), "mg")
        print("Focus:", self.person.day.focus_minutes, "min")
        print("Stress:", self.person.day.stress)
        print("Screen:", self.person.day.screen_minutes, "min")
        print("Performance score:", self.performance_score(self.person.day))
        print("Recommendation:")
        for action, reason, category, severity in self.person.day.recommendation():
            print(f"- [{severity.upper()} | {category.upper()}] {action}")
            print(f"  because: {reason}")

        last = load_last_day(self.person.day.date)

        print("Delta vs yesterday:")
        if last:
            today = {
                "performance_score": self.performance_score(self.person.day),
                "focus_minutes": self.person.day.focus_minutes,
                "caffeine": self.person.day.total_caffeine(),
            }
            for line in compute_delta(today, last):
                print(f"• {line}")
        else:
            print("• No prior day to compare against")
        print("Cortisol timing:")
        ct = self.person.day.cortisol

        if ct and ct.spike_achieved:
            print(f"• Cortisol spike achieved ({ct.spike_cause})")
        elif ct and ct.late_spike:
            print("• You spiked too late")
        else:
            print("• You still need a cortisol spike today")
            
#Put this in Feb 8
        print("Evening suppression:")
        if ct and not ct.late_activation:
            print("• Cortisol suppression intact")
        else:
            print(f"• Late cortisol activation detected ({ct.late_activation_cause})")

            print("Daily verdict:")
            if ct and ct.spike_achieved and not ct.late_activation:
                print("• Circadian timing aligned today")
            elif ct and not ct.spike_achieved:
                print("• Morning timing misaligned")
            elif ct and ct.late_activation:
                print("• Evening timing misaligned")
            else:
                print("• Mixed signals today")

        print("Weekly signal:")
        print(weekly_circadian_signal())









        

            
        
class Day:
    def __init__(self, date):
        self.date = date
        self.sleep = None
        self.training = 0
        self.caffeine = []
        self.light = []
        self.focus_minutes = 0
        self.stress = 0 #0-5 scale
        self.screen_minutes = 0 #total minutes today
        self.cortisol = None
    def log_focus(self, minutes):
        self.focus_minutes += minutes
    def log_sleep(self, sleep_session):
        self.sleep = sleep_session
    def log_training(self, intensity):
        self.training = intensity
    def log_caffeine(self, mg, hour):
        self.caffeine.append((mg, hour))
    def log_light(self, hour, minutes):
        self.light.append((hour, minutes))
    def log_stress(self, level):
        self.stress += level
    def log_screen(self, minutes):
        self.screen_minutes += minutes
    def total_caffeine(self):
        return sum(mg for mg, _ in self.caffeine)
    def evaluate_cortisol(self):
        if not self.cortisol:
            return

        # Morning spike evaluation
        for mg, hour in self.caffeine:
            self.cortisol.register_spike(hour, cause="caffeine")
            self.cortisol.register_evening_activation(hour, cause="caffeine")

        for hour, _ in self.light:
            self.cortisol.register_spike(hour)

        # Evening suppression evaluation
        for mg, hour in self.caffeine:
            self.cortisol.register_evening_activation(hour)

        for hour, _ in self.light:
            self.cortisol.register_spike(hour, cause="light")
            self.cortisol.register_evening_activation(hour, cause="light")
            
    def log_morning_activation(self, hour):
        if self.cortisol:
            self.cortisol.register_spike(hour, cause="explicit")





    
    def recommendation(self):
        recs = []

        if self.person.sleep_debt < -0.5:
            recs.append((
                "Go to bed 30–45 min earlier tonight",
                "Sleep debt below optimal range increases recovery volatility",
                "sleep",
                "high"
            ))

        if self.screen_minutes > 30:
            recs.append((
                "Cut evening screen time by 20 min",
                "High screen exposure delays melatonin onset",
                "screen",
                "medium"
            ))

        if self.total_caffeine() > 300:
            recs.append((
                "Cap caffeine at 300 mg tomorrow",
                "Excess caffeine worsens sleep pressure and HRV",
                "caffeine",
                "medium"
            ))

        if self.focus_minutes < 30:
            recs.append((
                "Schedule a 30–45 min deep work block",
                "Focused work below daily minimum reduces cognitive momentum",
                "focus",
                "high"
            ))

        if self.stress >= 3:
            recs.append((
                "Add a 10 min downshift (walk, breath, stretch)",
                "Elevated stress suppresses recovery systems",
                "stress",
                "medium"
            ))

        if not recs:
            recs.append((
                "Maintain current routine",
                "All systems operating within target ranges",
                "baseline",
                "low"
            ))

        # sort by severity (high → low)
        recs.sort(key=lambda r: SEVERITY_RANK[r[3]], reverse=True) #r = one recommendation tuple,
                                                                   #r[3] looks at severity tuple and uses corresponding label
            
                                                                    #lambda r: severity rank is like calling the method and returning the severity score
        # cap to top 2
        return recs[:2]
    
class CortisolTiming:
    def __init__(self, sunrise_time, suppression_start):
        self.sunrise_time = sunrise_time

        # Morning spike
        self.spike_cutoff = 9.5  # 9:30am
        self.spike_achieved = False
        self.spike_time = None
        self.spike_cause = None
        self.late_spike = False

        # Evening suppression
        self.suppression_start = suppression_start
        self.late_activation = False
        self.late_activation_cause = None

    def register_spike(self, hour, cause="unspecified"):
        if self.spike_achieved:
            return  # first cause only

        if hour <= self.spike_cutoff:
            self.spike_achieved = True
            self.spike_time = hour
            self.spike_cause = cause
        else:
            self.late_spike = True

    def register_evening_activation(self, hour, cause="unspecified"):
        if self.late_activation:
            return  # first cause only

        if hour >= self.suppression_start:
            self.late_activation = True
            self.late_activation_cause = cause

        


def new_manager():
    circadian = CircadianRhythm("optimal")
    keenan = Person("Keenan", circadian)
    return SleepManager(keenan)




def log_morning(day, sleep_start, sleep_end, caffeine_mg, caffeine_time, light_minutes, training):
    day.log_sleep(SleepSession(sleep_start, sleep_end, "good"))
    day.log_training(training)
    day.log_caffeine(caffeine_mg, caffeine_time)
    day.log_light(7, light_minutes)

def weekly_circadian_signal(days=7):
    try:
        with open("log.json", "r") as f:
            entries = [json.loads(line) for line in f.readlines()]
    except FileNotFoundError:
        return "• Not enough data for weekly signal"

    recent = entries[-days:]

    aligned = 0
    morning_missed = 0
    evening_missed = 0

    for d in recent:
        spike = d.get("cortisol_spike", False)
        late = d.get("late_activation", False)

        if spike and not late:
            aligned += 1
        elif not spike:
            morning_missed += 1
        elif late:
            evening_missed += 1

    if aligned >= days * 0.7:
        return "• Circadian timing stable this week"
    elif morning_missed > evening_missed:
        return "• Morning timing drifting later this week"
    elif evening_missed > morning_missed:
        return "• Evening activation accumulating this week"
    else:
        return "• Mixed circadian signals this week"

def detect_patterns(logs):
    insights = []

    # Example: caffeine timing vs performance
    late_caf_days = [d for d in logs if any(h >= 14 for _, h in d["caffeine_events"])]
    early_caf_days = [d for d in logs if all(h < 14 for _, h in d["caffeine_events"])]

    if late_caf_days and early_caf_days:
        avg_late = sum(d["performance_score"] for d in late_caf_days) / len(late_caf_days)
        avg_early = sum(d["performance_score"] for d in early_caf_days) / len(early_caf_days)

        if avg_late < avg_early:
            insights.append("Late caffeine correlates with lower performance")

    return insights

def predict_performance(day, person):
    score = 0
    
    score += person.energy * 0.4
    score += min(day.focus_minutes, 180) / 180 * 30
    score -= day.stress
    score -= min(day.screen_minutes, 120) / 120 * 10

    # NEW: penalties based on behavior BEFORE it happens
    if any(h >= 14 for _, h in day.caffeine):
        score -= 5

    return max(0, round(score, 1))

def generate_ai_insights(logs):
    prompt = f"""
    Here is 14 days of human performance data:
    {logs}

    Identify patterns that affect sleep, energy, and performance.
    Be specific and causal.
    """

    # send to OpenAI API



from datetime import date

SUNRISE_TIME = 6.85
SUPPRESSION_START = 19.5  # 7:30pm (your decision)

manager = new_manager()
day = Day(date.today().isoformat())
day.cortisol = CortisolTiming(SUNRISE_TIME, SUPPRESSION_START)


# ---- Daily Snapshot inputs (edit only here) ----
SLEEP_START = 21.08
SLEEP_END = 6.17
CAFFEINE_MG = 120
CAFFEINE_TIME = 7.50
LIGHT_MINUTES = 20
TRAINING = 2
FOCUS_MIN = 60
STRESS = 1
SCREEN_MIN = 0
# Explicit morning activation (sunlight + movement)
day.log_morning_activation(6.67)



log_morning(day, SLEEP_START, SLEEP_END, CAFFEINE_MG, CAFFEINE_TIME, LIGHT_MINUTES, TRAINING)
day.log_focus(FOCUS_MIN)
day.log_stress(STRESS)
day.log_screen(SCREEN_MIN)

# ---- RUN MODEL ----
manager.run_day(day)
manager.render_summary()
manager.save_day(day)














        
    

