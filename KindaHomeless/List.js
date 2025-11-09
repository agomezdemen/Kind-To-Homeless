import {StyleSheet, View, Text, ScrollView, ActivityIndicator} from 'react-native';
import BottomSheet, { BottomSheetView , BottomSheetScrollView} from '@gorhom/bottom-sheet';

import React, {useRef, useMemo, useCallback, useState} from "react";
import "./global.css";

export default function List({markers, selectedMarker, setSelectedMarker}) {
    // ref
    const bottomSheetRef = useRef(null);
    const snapPoints = useMemo(() => ['30%', '50%', '80%'], []);
    // callbacks
    const handleSheetChanges = useCallback((index) => {
        console.log('handleSheetChanges', index);
    }, []);

    const handleItemPress = useCallback((item, index, count) => {
        setSelectedMarker(item);
        // Expand to the middle snap point (50%) if not last two elements
        console.log(count + " " + index);
        if (count > 2 && index < count - 2) {
            bottomSheetRef.current?.snapToIndex(2);
        }
    }, [setSelectedMarker]);

    return (
            <BottomSheet
                ref={bottomSheetRef}
                snapPoints={snapPoints}
                maxDynamicContentSize={200}
                onChange={handleSheetChanges}
            >
                <BottomSheetScrollView className="pt-4 rounded-3xl w-full" style={styles.contentContainer}>
                    {markers.map((item, index) => {
                        const isSelected = selectedMarker && selectedMarker.id === item.id;
                        const count = markers.length;
                        var color = "";
                        var borderColor = "";
                        var pressedColor = "";
                        switch (item.feature_type) {
                            case "place_of_worship":
                                color = "bg-pink-700";
                                borderColor = "border-t-pink-400";
                                pressedColor = "bg-pink-800";
                                break;
                            case "welfare":
                            case "outreach":
                                color = "bg-sky-700";
                                borderColor = "border-t-sky-400";
                                pressedColor = "bg-sky-800";
                                break;
                            case "clothing_bank":
                            case "laundry":
                                color = "bg-purple-700";
                                borderColor = "border-t-purple-400";
                                pressedColor = "bg-purple-800";
                                break;
                            case "drinking_water":
                            case "water_tap":
                                color = "bg-teal-700";
                                borderColor = "border-t-teal-400";
                                pressedColor = "bg-teal-800";
                                break;
                            case "toilets":
                                color = "bg-orange-700";
                                borderColor = "border-t-orange-400";
                                pressedColor = "bg-orange-800";
                                break;
                            case "food_bank":
                            case "soup_kitchen":
                                color = "bg-amber-700";
                                borderColor = "border-t-amber-400";
                                pressedColor = "bg-amber-800";
                                break;
                            case "shower":
                                color = "bg-blue-700";
                                borderColor = "border-t-blue-400";
                                pressedColor = "bg-blue-800";
                                break;
                            default:
                                color = "bg-emerald-700";
                                borderColor = "border-t-emerald-400";
                                pressedColor = "bg-emerald-800";
                        }
                        return (
                            <View
                                onTouchEnd={() => handleItemPress(item, index, count)}
                                key={index}
                                className={`${borderColor} rounded-2xl border-t-2 mt-4 p-4 ${
                                    isSelected ? pressedColor : color
                                }`}
                            >
                                <View className="w-full left-4 flex">
                                    <Text className="text-4xl text-white">{item.name}</Text>
                                    <Text className="text-xl text-gray-200">{item.feature_type.replaceAll('_', ' ')} | {item.distance} miles</Text>
                                    <Text className="text-lg w-64 text-gray-200">{item.address}</Text>
                                </View>
                            </View>
                        );
                    })}
                        {markers.length === 0 && (
                            <View className="h-full w-full justify-center items-center">
                                <View className="absolute justify-center top-1/2 items-center text-center w-full text-lg">
                                    <ActivityIndicator size="large" />
                                    <Text>Getting location and fetching nearby data…</Text>
                                </View>

                            </View>
                        )}
                    <View className="h-36"></View>
                </BottomSheetScrollView>
            </BottomSheet>

    );
}
const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: 'grey',
    },
    contentContainer: {
        flex: 1,
        padding: 16,
        paddingBottom: 64,
        borderRadius: 35,
    },
});

// <View style={{maxHeight:"550"}} className=" w-full justify-center items-center flex bg-white border-t-emerald-400 border-t-2 absolute bottom-24">
//     <View className="h-0 m-3 w-16 border-b-2  border-b-gray-300"></View>
//     <ScrollView className="rounded-3xl w-11/12">
//         {markers.map((item, index) => {
//                 return (
//                     <View key={index} className="border-t-emerald-400 bg-emerald-700 rounded-2xl border-t-2 mt-4 p-4">
//                         <View className="w-full left-4 flex">
//                             <Text className="text-4xl text-white">{item.title}</Text>
//                             <Text className="text-xl text-white">{item.description}</Text>
//                             <Text className="text-lg text-white">{item.latitude} {item.longitude}</Text>
//                         </View>
//                         <View >
//
//                         </View>
//                     </View>
//                 )
//             }
//         )}
//     </ScrollView>
// </View>