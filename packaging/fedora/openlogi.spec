Name:           openlogi
Version:        0.8.20
Release:        1%{?dist}
Summary:        Logitech device settings with a Linux status notifier tray
License:        MIT AND Apache-2.0 AND 0BSD AND BSD-2-Clause AND BSD-3-Clause AND ISC AND Unicode-3.0 AND Zlib AND CC0-1.0 AND MPL-2.0 AND Unlicense AND bzip2-1.0.6 AND CDLA-Permissive-2.0
URL:            https://github.com/Pioterr665/OpenLogiTray
# Generated with prepare-source.py; includes locked, vendored Cargo sources.
Source0:        openlogi-%{version}.tar.gz
BuildRequires:  rust >= 1.99
BuildRequires:  cargo >= 1.99
BuildRequires:  gcc-c++
BuildRequires:  clang-devel
BuildRequires:  pkgconfig(fontconfig)
BuildRequires:  pkgconfig(libudev)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(xkbcommon-x11)
BuildRequires:  pkgconfig(x11-xcb)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(libzstd)
BuildRequires:  kernel-headers
BuildRequires:  systemd-rpm-macros
BuildRequires:  desktop-file-utils
BuildRequires:  dbus-daemon
Requires:       hicolor-icon-theme
Requires:       dbus

%description
Local Logitech HID++ device configuration, button remapping and a session-bus
StatusNotifierItem tray for KDE and GNOME with an AppIndicator extension.
This fork uses independent MIT-licensed artwork.

%prep
%autosetup

%build
export CARGO_HOME="$PWD/.cargo-home"
export OPENLOGI_THEMES_DIR="$PWD/upstream-themes"
cargo build --release --frozen -p openlogi -p openlogi-desktop -p openlogi-agent -p openlogi-overlay --bin openlogi --bin openlogi-desktop --bin openlogi-agent --bin openlogi-overlay

%install
for binary in openlogi openlogi-desktop openlogi-agent openlogi-overlay; do
    install -Dpm0755 target/release/$binary %{buildroot}%{_bindir}/$binary
done
install -Dpm0644 packaging/linux/desktop/openlogi.desktop %{buildroot}%{_datadir}/applications/openlogi.desktop
install -Dpm0644 packaging/linux/systemd/openlogi-agent.service %{buildroot}%{_userunitdir}/openlogi-agent.service
install -Dpm0644 packaging/linux/udev/70-openlogi.rules %{buildroot}%{_udevrulesdir}/70-openlogi.rules
for size in 16 32 48 64 128 256 512; do
    install -Dpm0644 design/icon/openlogi-$size.png %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/openlogi.png
done

%check
export CARGO_HOME="$PWD/.cargo-home"
export OPENLOGI_THEMES_DIR="$PWD/upstream-themes"
cargo test --frozen -p openlogi-agent --bin openlogi-agent tray_linux::tests
dbus-run-session -- cargo test --frozen -p openlogi-ipc private_bus_lifecycle -- --ignored
desktop-file-validate %{buildroot}%{_datadir}/applications/openlogi.desktop

%post
%systemd_user_post openlogi-agent.service

%preun
%systemd_user_preun openlogi-agent.service

%postun
%systemd_user_postun_with_restart openlogi-agent.service

%files
%license LICENSE-MIT LICENSE-APACHE design/LICENSE bundled-licenses bundled-licenses.json
%doc README.md
%{_bindir}/openlogi
%{_bindir}/openlogi-desktop
%{_bindir}/openlogi-agent
%{_bindir}/openlogi-overlay
%{_datadir}/applications/openlogi.desktop
%{_datadir}/icons/hicolor/*/apps/openlogi.png
%{_userunitdir}/openlogi-agent.service
%{_udevrulesdir}/70-openlogi.rules

%changelog
* Mon Nov 02 2026 OpenLogiTray contributors - 0.8.20-1
- Add native Fedora build with independent artwork and vendored sources
