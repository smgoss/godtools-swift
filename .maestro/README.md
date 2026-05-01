# GodTools Maestro UI Tests

Black-box UI test suite that drives the GodTools iOS app through accessibility identifiers and deep links. Designed to remain valid across rendering-engine ports — no XCTest, no in-app launchEnvironment plumbing, just deep links + accessibility IDs.

## How it works

Every flow follows the same pattern:

1. `launchApp` (with `clearState: true` for hermetic state)
2. Conditionally dismiss onboarding via `helpers/dismiss_onboarding.yaml`
3. `openLink` to a godtools deep link (defined in `GodToolsDeepLinkingManifest.swift`)
4. Assert the expected screen by its `AccessibilityStrings.Screen` id
5. Tap buttons by their `AccessibilityStrings.Button` id and assert resulting screens

Selector ids come from `godtools/App/Share/Application/Accessibility/AccessibilityStrings.swift`. Keep that file in sync with new screens/buttons as the suite grows.

## Why not Maestro `arguments:`?

The existing XCUITests use `app.launchEnvironment` to pass `UITests.isUITests=true` and a deep-link URL into `ProcessInfo.processInfo.environment`. Maestro on iOS simulator runs `xcrun simctl launch <bundle> -<key> <value>`, which lands the args in `ProcessInfo.processInfo.arguments`, not environment. The `arguments:` field in Maestro YAML therefore cannot reach the existing `UITestsLaunchEnvironment` reader. Rather than fork the readers, this suite drives the app via post-launch `openLink` against the same deep links the app already routes for production.

## Onboarding handling

`launchApp` with `clearState: true` puts the app in first-launch state and shows onboarding. Two patterns are supported:

- **Onboarding flows** (`flows/onboarding/*`) keep onboarding and exercise it directly.
- **All other flows** call `helpers/dismiss_onboarding.yaml`, which conditionally walks through onboarding if it's currently visible (no-op otherwise), then proceeds to the deep link of interest.

If you prefer a different model (e.g. preserve state across runs by setting `clearState: false`), swap the helper for a one-time onboarding completion flow and remove `clearState: true` from each launch step.

## Install Maestro

```sh
brew tap mobile-dev-inc/tap
brew install maestro
# or
curl -fsSL "https://get.maestro.mobile.dev" | bash
```

## Run

Boot a simulator and install the godtools app first (build & run from Xcode at least once for the `org.cru.godtools` bundle). Then from the repo root:

```sh
# all flows
maestro test .maestro

# one folder
maestro test .maestro/flows/menu

# one flow
maestro test .maestro/flows/dashboard/01_initial_favorites.yaml

# interactive authoring
maestro studio
```

To target the beta build, change `appId` in `.maestro/config.yaml` (and the deep-link host in helper flows) to `org.cru.godtools.beta`.

## Layout

```
.maestro/
├── config.yaml
├── README.md
├── helpers/
│   ├── dismiss_onboarding.yaml          # conditional walk-through of onboarding
│   ├── launch_to_dashboard_favorites.yaml
│   ├── launch_to_dashboard_tools.yaml
│   ├── launch_to_menu.yaml
│   ├── launch_to_language_settings.yaml
│   ├── launch_to_app_languages.yaml
│   ├── launch_to_onboarding.yaml
│   ├── launch_to_tool_details.yaml
│   └── launch_to_tract.yaml
└── flows/
    ├── onboarding/
    ├── dashboard/
    ├── menu/
    ├── language_settings/
    ├── choose_app_language/
    ├── tool_details/
    ├── learn_to_share/
    └── tool_screen_share/
```

Numeric prefixes (`01_`, `02_`) on flow filenames give a stable ordering when running a folder, but each flow is independent — one failure doesn't block the rest.

## Adding a new flow

1. If the screen has no accessibility id, add one to `AccessibilityStrings.Screen` and place an `AccessibilityScreenElementView` inside the screen body.
2. If a button has no accessibility id, add to `AccessibilityStrings.Button` and tag the view.
3. If you need a launch shortcut for that screen, register a deep link path in `GodToolsDeepLinkingManifest` + parser.
4. Drop a `*.yaml` flow into the appropriate `flows/<feature>/` subfolder. Reuse helpers; don't repeat onboarding-dismiss logic inline.
