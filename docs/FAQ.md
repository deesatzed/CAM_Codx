# FAQ

## What is this?

CAM_Codx is the Codex-native workflow hub for CAM. It contains goals,
templates, onboarding docs, and adapter guidance for using CAM outputs from
Codex.

## Why are there multiple CAM repos?

The repos have different jobs. CAM_CAM is the runtime engine. CAM_Codx is the
Codex workflow hub. Generated product repos are standalone outputs.

## Why not one monorepo?

The current evidence favors separate ownership: runtime code and local
databases stay in CAM_CAM, public Codex workflows stay in CAM_Codx, and
generated products keep their own repo history and tests.

## What repo should a Codex user start with?

Start with CAM_Codx.

## What repo should a runtime contributor start with?

Start with CAM_CAM.

## What is a generated product repo?

It is a separate repo created from CAM/Codex evidence and goals. The packet is
not the product. The product repo needs its own runtime code, tests, README,
provenance, and smoke command.

## How do Claude Code and Grok Build fit?

They are adapter surfaces. They can consume CAM packets and source receipts,
but they should preserve the same read-only source boundaries and standalone
product proof gates.
