# PurpleWave Patch Notes

Minimal source patch:

```scala
// src/Lifecycle/PurpleWave.scala
override def onFrame(): Unit = {
  tryCatch(() => Commander.CommanderQueueConsumer.poll("runtime/commands.jsonl"))
  ...
}
```

Production bias example:

```scala
val workerGoalBonus =
  if (Commander.CommanderIntent.hasHardGoal("produce_worker")) 1.0 else 0.0
```

Squad bias example:

```scala
val attackThresholdBias = Commander.CommanderIntent.aggressionBias * -0.25
val harassPreference = Commander.CommanderIntent.harassBias
```

Micro doctrine example:

```scala
if (Commander.CommanderIntent.current.activeCommands.exists(_.action == "set_micro_doctrine")) {
  // Apply target filter / retreat threshold changes near Micro.Targeting and Retreat decisions.
}
```
