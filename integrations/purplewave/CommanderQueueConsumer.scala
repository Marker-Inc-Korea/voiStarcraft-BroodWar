package Commander

import java.nio.charset.StandardCharsets
import java.nio.file.{Files, Paths}
import java.util.Arrays
import scala.collection.JavaConverters._
import mjson.Json

object CommanderQueueConsumer {
  private var byteOffset: Long = 0L

  def poll(pathString: String = "runtime/commands.jsonl"): Unit = {
    val path = Paths.get(pathString)
    if (!Files.exists(path)) return
    val bytes = Files.size(path)
    if (bytes < byteOffset) byteOffset = 0L
    if (bytes == byteOffset) return

    val allBytes = Files.readAllBytes(path)
    val newBytes = Arrays.copyOfRange(allBytes, byteOffset.toInt, allBytes.length)
    byteOffset = bytes

    val lines = new String(newBytes, StandardCharsets.UTF_8)
      .split("\n")
      .map(_.trim)
      .filter(_.nonEmpty)
      .toVector

    val commands = lines
      .flatMap(parseCommand)
      .toVector

    if (commands.nonEmpty) {
      CommanderIntent.update(applyCommands(CommanderIntent.current, commands))
      CommanderTelemetry.commandStatus(commands.map(_.id), "active", "accepted by PurpleWave queue consumer")
    }
  }

  private def parseCommand(line: String): Option[CommanderCommand] = {
    try {
      val obj = Json.read(line)
      Some(
      CommanderCommand(
        id = stringField(obj, "command_id", "unknown"),
        commandType = stringField(obj, "command_type", "unknown"),
        action = stringField(obj, "action", "unknown"),
        payload = payloadMap(obj)))
    } catch {
      case _: Exception => None
    }
  }

  private def stringField(obj: Json, key: String, fallback: String): String =
    if (obj.has(key) && ! obj.at(key).isNull) obj.at(key).asString else fallback

  private def payloadMap(obj: Json): Map[String, Any] = {
    if (! obj.has("payload") || obj.at("payload").isNull) return Map.empty
    val payload = obj.at("payload")
    val values = scala.collection.mutable.Map.empty[String, Any]
    if (payload.has("race")) values("race") = payload.at("race").asString
    if (payload.has("plan")) values("plan") = payload.at("plan").asString
    if (payload.has("style") && ! payload.at("style").isNull) {
      val style = payload.at("style")
      values("style") = Map(
        "aggression" -> doubleField(style, "aggression", 0.5),
        "harass" -> doubleField(style, "harass", 0.5),
        "economy_greed" -> doubleField(style, "economy_greed", 0.5),
        "defensive_safety" -> doubleField(style, "defensive_safety", 0.5),
        "all_in_commitment" -> doubleField(style, "all_in_commitment", 0.2))
    }
    values.toMap
  }

  private def doubleField(obj: Json, key: String, fallback: Double): Double =
    if (obj.has(key) && ! obj.at(key).isNull) obj.at(key).asDouble else fallback

  private def applyCommands(contract: CommanderContract, commands: Vector[CommanderCommand]): CommanderContract = {
    commands.foldLeft(contract) { (next, command) =>
      command.action match {
        case "set_race" =>
          next.copy(race = command.payload.get("race").map(_.toString).getOrElse(next.race), activeCommands = upsert(next.activeCommands, command))
        case "set_style" =>
          next.copy(style = mergeStyle(next.style, command.payload), activeCommands = upsert(next.activeCommands, command))
        case _ =>
          next.copy(activeCommands = upsert(next.activeCommands, command))
      }
    }
  }

  private def upsert(commands: Vector[CommanderCommand], command: CommanderCommand): Vector[CommanderCommand] =
    commands.filterNot(_.id == command.id) :+ command

  private def mergeStyle(style: CommanderStyle, payload: Map[String, Any]): CommanderStyle = {
    val stylePayload = payload.get("style").collect { case data: Map[String @unchecked, Any @unchecked] => data }.getOrElse(Map.empty)
    def number(key: String, fallback: Double): Double = stylePayload.get(key).map(_.toString.toDouble).getOrElse(fallback)
    style.copy(
      aggression = number("aggression", style.aggression),
      harass = number("harass", style.harass),
      economyGreed = number("economy_greed", style.economyGreed),
      defensiveSafety = number("defensive_safety", style.defensiveSafety),
      allInCommitment = number("all_in_commitment", style.allInCommitment))
  }
}
