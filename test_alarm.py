"""Smoke test: add -> appears pending -> dismiss -> marked done."""

import alarm


def demo():
    alarm.save_alarms([])  # start clean

    alarm.save_alarms([{"id": 1, "time": "07:30", "label": "test", "status": "pending"}])
    alarms = alarm.load_alarms()
    assert alarms[0]["status"] == "pending", "new alarm should start pending"

    alarms[0]["status"] = "done"  # simulate a dismiss
    alarm.save_alarms(alarms)
    assert alarm.load_alarms()[0]["status"] == "done", "dismissed alarm should be marked done"

    alarm.save_alarms([])  # clean up
    print("ok")


if __name__ == "__main__":
    demo()
