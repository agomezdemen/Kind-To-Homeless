import { StyleSheet, View, ActivityIndicator, Text, Platform } from 'react-native';
import { ButtonGroup } from '@rneui/themed';
import { Icon } from '@rneui/themed';

import React, {Component, useState} from "react";
import "./global.css";

export default function Navbar() {
    const [selectedIndex, setSelectedIndex] = useState(0);
        return (
            <View className="h-24 w-full bg-emerald-900 border-t-emerald-100 border-2 absolute pb-2 bottom-0">
                <ButtonGroup
                    containerStyle={{ height: '80%', backgroundColor: 'transparent' , borderWidth: 0 }}
                    buttonStyle={{backgroundColor:'transparent', transitionDelay: 20}}
                    selectedButtonStyle={{ backgroundColor: 'rgba(0, 0, 0, 0.2)' }}
                    buttons={[
                        <Icon name="map" color="#ffffff" />,
                        <Icon name="format-align-center" color="#ffffff"/>,
                    ]}
                    selectedIndex={selectedIndex}
                    onPress={(value) => setSelectedIndex(value)}
                />
            </View>
        );
}
