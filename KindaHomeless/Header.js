import { SearchBar } from '@rneui/themed';
import { StyleSheet, View, ActivityIndicator, Text, Platform } from 'react-native';
import React, {Component} from "react";
import "./global.css";



export default class Header extends Component {
    state = {
        search: '',
    };

    updateSearch = (search) => {
        this.setState({ search });
    };

    render() {
        const {search} = this.state;
        return (
            <View className="h-32 w-full bg-emerald-900 absolute pt-12 p-4">
                <View></View>
                <SearchBar
                    placeholder="Search POI's"
                    onChangeText={this.updateSearch}
                    value={search}
                    platform="android"
                    containerStyle={{"backgroundColor":"transparent"}}
                    inputContainerStyle={{
                        "borderRadius": 30,
                        "backgroundColor": "ivory"
                    }}
                        ></SearchBar>
            </View>
        );
    }
}
