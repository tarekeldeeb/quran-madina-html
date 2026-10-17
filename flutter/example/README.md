# quran_madina_flutter example

```bash
flutter create .                          # add the platform folders (android, ios, web, ...)
dart run quran_madina_flutter:bundle      # copy the library in, for the offline switch
flutter run                               # or: flutter run -d chrome
```

On Android and iOS the offline switch needs the local-server settings from the package
README (`usesCleartextTraffic` / `NSAllowsLocalNetworking`).
