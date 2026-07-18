#!/usr/bin/tclsh
# IOU router Tcl bootstrap and controller registration.
#
# DHCP option 67 must identify iou_router_autoinstall.cfg. AutoInstall
# applies that IOS configuration, whose one-shot EEM applet runs this file
# directly from TFTP with tclsh.

set CONTROLLER_HOST "10.10.0.2"
set CONTROLLER_PORT 8000
set CONTROLLER_PATH "/device/register"

set SSH_USER "ansible"
set SSH_PASSWORD "Ansible@123"
set DOMAIN_NAME "ztp.local"
set RSA_BITS 2048

set MANAGEMENT_INTERFACE "Ethernet0/0"
set INSTALL_APPLET "INSTALL-IOU-ROUTER-ZTP"

set IP_WAIT_ATTEMPTS 5
set IP_WAIT_SECONDS 2
set REGISTER_ATTEMPTS 3
set REGISTER_RETRY_SECONDS 2


proc log_message {message} {
    puts "IOU-ROUTER-ZTP: $message"
}


proc apply_config {commands} {
    set invocation [linsert $commands 0 ios_config]
    if {[catch {eval $invocation} result]} {
        log_message "configuration failed: $result"
        return 0
    }
    return 1
}


proc get_interface_mac {interface_name} {
    set output ""
    if {[catch {set output [exec "show interfaces $interface_name"]} error]} {
        log_message "cannot read MAC from $interface_name: $error"
        return ""
    }

    if {![regexp -nocase {address is ([0-9a-f]{4})\.([0-9a-f]{4})\.([0-9a-f]{4})} $output match part1 part2 part3]} {
        return ""
    }

    set compact [string tolower "$part1$part2$part3"]
    return [format "%s:%s:%s:%s:%s:%s" \
        [string range $compact 0 1] \
        [string range $compact 2 3] \
        [string range $compact 4 5] \
        [string range $compact 6 7] \
        [string range $compact 8 9] \
        [string range $compact 10 11]]
}


proc get_interface_ip {interface_name} {
    set output ""
    if {[catch {set output [exec "show ip interface brief"]} error]} {
        log_message "cannot read IP from $interface_name: $error"
        return ""
    }

    foreach line [split $output "\n"] {
        set trimmed [string trim $line]
        if {[string first $interface_name $trimmed] != 0} {
            continue
        }
        if {[regexp {([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)} $trimmed ip_address]} {
            return $ip_address
        }
    }
    return ""
}


proc wait_for_interface_ip {interface_name attempts delay_seconds} {
    for {set attempt 1} {$attempt <= $attempts} {incr attempt} {
        set ip_address [get_interface_ip $interface_name]
        if {$ip_address != "" && $ip_address != "0.0.0.0"} {
            return $ip_address
        }
        log_message "waiting for DHCP on $interface_name ($attempt/$attempts)"
        after [expr {$delay_seconds * 1000}]
    }
    return ""
}


proc rsa_key_exists {} {
    set output ""
    if {[catch {set output [exec "show crypto key mypubkey rsa"]}]} {
        return 0
    }
    return [expr {[string first "Key name" $output] >= 0 || [string first "Key Data" $output] >= 0}]
}


proc ensure_rsa_key {rsa_bits} {
    if {[rsa_key_exists]} {
        log_message "RSA key already exists"
        return 1
    }

    log_message "generating a $rsa_bits-bit RSA key"
    if {[apply_config [list "crypto key generate rsa general-keys modulus $rsa_bits"]]} {
        return 1
    }

    if {$rsa_bits != 1024} {
        log_message "retrying RSA key generation with 1024 bits for older IOU images"
        return [apply_config [list "crypto key generate rsa general-keys modulus 1024"]]
    }
    return 0
}


proc post_registration {host port path body} {
    set sock ""
    if {[catch {set sock [socket $host $port]} error]} {
        log_message "HTTP connection failed: $error"
        return 0
    }

    if {[catch {
        fconfigure $sock -translation binary -buffering none
        puts -nonewline $sock "POST $path HTTP/1.0\r\n"
        puts -nonewline $sock "Host: $host:$port\r\n"
        puts -nonewline $sock "Content-Type: application/json\r\n"
        puts -nonewline $sock "Content-Length: [string length $body]\r\n"
        puts -nonewline $sock "Connection: close\r\n\r\n"
        puts -nonewline $sock $body
        flush $sock
        set response [read $sock]
        close $sock
    } error]} {
        catch {close $sock}
        log_message "HTTP request failed: $error"
        return 0
    }

    if {[regexp {HTTP/[0-9.]+ ([0-9]+)} $response match status_code] && $status_code >= 200 && $status_code < 300} {
        log_message "registration succeeded with HTTP $status_code"
        return 1
    }

    log_message "registration failed: $response"
    return 0
}


log_message "starting bootstrap"

# Remove the one-shot applet before saving so the bootstrap does not run on
# every reload.
apply_config [list "no event manager applet $INSTALL_APPLET"]

set mac_address [get_interface_mac $MANAGEMENT_INTERFACE]
set hostname "IOU-Router"
if {$mac_address != ""} {
    set compact_mac [string map {":" ""} $mac_address]
    set hostname "IOU-R-[string toupper [string range $compact_mac end-5 end]]"
}

apply_config [list "hostname $hostname"]
apply_config [list "ip domain-name $DOMAIN_NAME"]
apply_config [list "username $SSH_USER privilege 15 secret 0 $SSH_PASSWORD"]
apply_config [list "ip ssh version 2" "ip ssh time-out 30" "ip ssh authentication-retries 3"]
apply_config [list "line vty 0 4" "login local" "transport input ssh"]
apply_config [list "no service config"]

ensure_rsa_key $RSA_BITS

set ip_address [wait_for_interface_ip $MANAGEMENT_INTERFACE $IP_WAIT_ATTEMPTS $IP_WAIT_SECONDS]
if {$mac_address == ""} {
    set mac_address [get_interface_mac $MANAGEMENT_INTERFACE]
}

if {$ip_address == "" || $mac_address == ""} {
    log_message "registration skipped because management IP or MAC is unavailable"
    return
}

log_message "management interface $MANAGEMENT_INTERFACE has IP $ip_address and MAC $mac_address"

set json_body [format {{"ip_address":"%s","mac":"%s","os_type":"cisco_ios","status":"register","device_type":"router","username":"%s","password":"%s"}} \
    $ip_address $mac_address $SSH_USER $SSH_PASSWORD]

for {set attempt 1} {$attempt <= $REGISTER_ATTEMPTS} {incr attempt} {
    log_message "registering with controller ($attempt/$REGISTER_ATTEMPTS)"
    if {[post_registration $CONTROLLER_HOST $CONTROLLER_PORT $CONTROLLER_PATH $json_body]} {
        if {[catch {exec "write memory"} save_error]} {
            log_message "registration succeeded but configuration save failed: $save_error"
            return
        }
        log_message "configuration saved; AutoInstall is complete"
        return
    }
    if {$attempt < $REGISTER_ATTEMPTS} {
        after [expr {$REGISTER_RETRY_SECONDS * 1000}]
    }
}

log_message "registration failed after $REGISTER_ATTEMPTS attempts"
