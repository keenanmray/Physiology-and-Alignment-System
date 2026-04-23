"""Sleep System V3 CLI runner."""

from datetime import date

from sleep_engine import (
    DayInput,
    DailyResult,
    Person,
    SleepSession,
    SleepSystemEngine,
    compare_to_previous,
    load_logs,
    save_log,
    weekly_insights,
)


def print_report(result: DailyResult, deltas: list[str], weekly: list[str]) -> None:
    print("\nSLEEP SYSTEM V3")
    print("Behavioral Performance Engine")
    print("-" * 36)
    print("Date:", result.date)
    print("Sleep Hours:", result.sleep_hours)
    print("Energy:", result.energy)
    print("Recovery:", result.recovery)
    print("Sleep Debt:", result.sleep_debt)
    print("Circadian Status:", result.circadian_status)
    print("Circadian Shift:", result.circadian_shift, "minutes")
    print("Performance Score:", result.performance_score)
    print("Tomorrow Score:", result.tomorrow_score)

    print("\nDaily Insights")
    for insight in result.insights:
        print("-", insight)

    print("\nTop Recommendations")
    for recommendation in result.recommendations:
        print("-", recommendation)

    print("\nDelta vs Previous Day")
    for delta in deltas:
        print("-", delta)

    print("\nWeekly Pattern Read")
    for insight in weekly:
        print("-", insight)


def main() -> None:
    logs = load_logs()
    person = Person(name="Keenan")
    engine = SleepSystemEngine(person)

    # Edit this block to log a new day.
    day = DayInput(
        day_date=date.today().isoformat(),
        sleep=SleepSession(start=21.25, end=6.25, quality="good"),
        caffeine_events=[(140, 8.0)],
        light_events=[(7.0, 20)],
        training_intensity=2,
        focus_minutes=120,
        stress=1,
        screen_minutes=45,
        movement_minutes=35,
        social_quality=4,
    )

    result = engine.run_day(day)
    deltas = compare_to_previous(result, logs)
    weekly = weekly_insights(logs + [result.to_log_dict(day)])

    print_report(result, deltas, weekly)
    save_log(result.to_log_dict(day))


if __name__ == "__main__":
    main()
