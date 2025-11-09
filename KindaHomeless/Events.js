import {StyleSheet, View, ActivityIndicator, Text, ScrollView, Platform, Linking} from 'react-native';
import { ButtonGroup } from '@rneui/themed';
import { Icon } from '@rneui/themed';

import React, {Component, useState} from "react";
import "./global.css";

export default function Events({searchQuery}) {
    const events = ['1','2','3','4','5','6','7','8','9'];

    const openInGoogleMaps = (latitude, longitude) => {
        const url = `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}`;
        Linking.openURL(url).catch(err => console.error("Couldn't load Google Maps", err));
    };

    return (
        <ScrollView  contentContainerStyle={{alignItems:"center",flex:1,gap:4}} className="h-full top-36 w-full flex gap-4 ">
            <Text className="text-6xl ">Events</Text>
            <View className="border-b-2 border-b-gray-200 w-1/2 h-0 mt-2 mb-2"/>
            {events.map((event, i) => (
                <View key={i} className="bg-emerald-900 m-2 w-10/12 rounded-2xl items-center flex p-4">
                    <Text className="text-white text-3xl">Title</Text>
                    <Text className="text-gray-200 text-xl">Date</Text>
                    <Text className="text-gray-200 text-lg">Summary</Text>
                    <View className="p-4 w-16 h-12 pb-0 mb-0 " onTouchEnd={() => {openInGoogleMaps(event.latitude, event.longitude)}}>
                        <Icon  name="map" color="white" />
                    </View>
                </View>
            ))}
            <View className="mb-64"></View>
        </ScrollView>
    );
}
