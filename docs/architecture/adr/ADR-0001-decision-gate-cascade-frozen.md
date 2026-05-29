# ADR-0001: Decision-Gate-Kaskade eingefroren

## Kontext

77 Decision-Check-Skripte und 76 Decision-Tests bildeten eine rekursive
Precondition-Kaskade. Diese Kaskade pruefte zunehmend Vorentscheidungen statt
lieferbarer Funktion und erhoehte die Verifikationskosten ohne entsprechenden
Produktfortschritt.

## Entscheidung

Die Decision-Gate-Kaskade wird eingefroren. Die zugehoerigen Skripte und Tests
wurden nach `archive/decision_gate_cascade/` verschoben und aus
`verify_bootstrap.py` sowie aus der aktiven pytest-Suite herausgeloest.

Zugehoerige Contract-Schemas, Contract-Instances und Architektur-Dokumente
bleiben als Daten-SSOT erhalten.

## Konsequenzen

`make verify` und die Test-Suite werden deutlich kleiner und konzentrieren sich
auf aktive, lieferbare Artefakte. Neue Decision-Gates duerfen nicht ohne neuen
ADR eingefuehrt werden.

## Referenz-Commit

`cfb7156`
