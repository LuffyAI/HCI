"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowUp, Delete, Keyboard, Lightbulb, Undo2 } from "lucide-react";

const getSuggestions = async (text: string, isWordCompletion: boolean): Promise<string[]> => {
  const endpoint = isWordCompletion ? "/suggest_word_completion" : "/suggest_next_word";
  try {
    const response = await fetch(`http://localhost:8000${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await response.json();
    return data.suggestions;
  } catch (error) {
    console.error("Error fetching suggestions:", error);
    return [];
  }
};

const sendMessageAPI = async (sender: string, text: string): Promise<void> => {
  try {
    await fetch("http://localhost:8000/send_message/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sender, text }),
    });
  } catch (error) {
    console.error("Error sending message:", error);
  }
};

const getLightbulbSuggestions = async (data: any): Promise<string[]> => {
  try {
    const response = await fetch("http://localhost:8000/lightbulb_click/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const result = await response.json();
    return result.suggestions || [];
  } catch (error) {
    console.error("Error fetching lightbulb suggestions:", error);
    return [];
  }
};

type Message = {
  text: string;
  sender: "user" | "other";
};

export default function Component() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isUpperCase, setIsUpperCase] = useState(false);
  const [isSpecialChar, setIsSpecialChar] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [useLightbulbSuggestions, setUseLightbulbSuggestions] = useState(false);
  const [lastIndex, setLastIndex] = useState(0);

  // Poll messages from the backend
  useEffect(() => {
    const pollMessages = async () => {
      const response = await fetch(`http://localhost:8000/get_messages/?start_index=${lastIndex}`);
      const newMessages = await response.json();
      if (newMessages.length > 0) {
        setMessages((prevMessages) => [...prevMessages, ...newMessages]);
        setLastIndex((prevIndex) => prevIndex + newMessages.length);
      }
    };

    const interval = setInterval(pollMessages, 1000);
    return () => clearInterval(interval);
  }, [lastIndex]);

  // Fetch suggestions (default or lightbulb)
  useEffect(() => {
    if (input && !useLightbulbSuggestions) {
      const isWordCompletion = input[input.length - 1] !== " ";
      const contextText = isWordCompletion
        ? input.split(" ").slice(-15).join(" ")
        : input.trim();
      getSuggestions(contextText, isWordCompletion).then(setSuggestions);
    } else if (!input && !useLightbulbSuggestions) {
      setSuggestions([]);
    }
  }, [input, useLightbulbSuggestions]);

  const handleLightbulbClick = async () => {
    console.log("Lightbulb clicked. Current lightbulb mode:", useLightbulbSuggestions);
  
    if (useLightbulbSuggestions) {
      // Turn off lightbulb suggestions and enable default suggestions
      setUseLightbulbSuggestions(false);
      setSuggestions([]); // Clear suggestions
      console.log("Lightbulb mode deactivated. Default suggestions re-enabled.");
      return;
    }
  
    // Prepare data for API
    const previousContext = messages
      .map((message) => `${message.sender === "user" ? "You" : "Other"}: ${message.text}`)
      .join(" ");
  
    const data = {
      previous_context: previousContext,
      user_current_input: input,
      context_mode: "",
      button_press: "Yellow",
      suggestions: [],
    };
  
    console.log("Sending data to lightbulb API:", data);
  
    try {
      // Call lightbulb API and wait for response
      const newSuggestions = await getLightbulbSuggestions(data);
  
      if (newSuggestions && newSuggestions.length > 0) {
        console.log("Lightbulb suggestions received:", newSuggestions);
        setUseLightbulbSuggestions(true); // Enable lightbulb mode
        setSuggestions(newSuggestions);  // Update suggestions in UI
      } else {
        console.warn("Lightbulb API returned an empty or invalid response:", newSuggestions);
        setSuggestions([]); // Clear suggestions if API returns no results
      }
    } catch (error) {
      console.error("Error fetching lightbulb suggestions:", error);
      setSuggestions([]); // Clear suggestions on error
    }
  };

  const handleKeyPress = (key: string) => {
    if (key === "backspace") {
      setInput(input.slice(0, -1));
    } else if (key === "undo") {
      setInput(input.slice(0, -1));
    } else if (key === "space") {
      setInput(input + " ");
    } else if (key === "send") {
      if (input.trim()) {
        sendMessageAPI("user", input.trim());
        setInput("");
      }
    } else {
      setInput(input + (isUpperCase ? key.toUpperCase() : key));
    }
  };

  const numberKeys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"];
  const letterKeys = [
    ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
    ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
    ["shift", "z", "x", "c", "v", "b", "n", "m", "backspace"],
    ["123", "space", "send"],
  ];
  const specialKeys = [
    ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")"],
    ["-", "_", "+", "=", "{", "}", "[", "]", "|", "\\"],
    [".", ",", "?", ":", ";", "undo", "backspace"],
    ["abc", "space", "send"],
  ];

  const keys = isSpecialChar ? specialKeys : letterKeys;

  return (
    <Card className="w-full max-w-lg mx-auto h-screen flex flex-col justify-between bg-white shadow-lg md:max-w-3xl">
      <div className="flex-grow h-1/2 overflow-y-auto p-4 bg-gray-100">
        {messages.map((message, index) => (
          <div key={index} className={`mb-2 flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}>
            <span
              className={`rounded-lg px-3 py-2 inline-block ${
                message.sender === "user" ? "bg-green-500 text-white" : "bg-blue-500 text-white"
              }`}
            >
              {message.text}
            </span>
          </div>
        ))}
      </div>
      <div className="p-2 bg-gray-200 border-t border-gray-300">
        <input
          type="text"
          value={input}
          readOnly
          className="w-full p-2 rounded-md bg-white focus:outline-none"
          placeholder="Type a message..."
        />
      </div>
      <div className="flex flex-wrap gap-2 justify-around p-2 bg-gray-300">
  {suggestions.map((suggestion, index) => (
    <Button
      key={index}
      variant="secondary"
      className="text-sm md:text-base px-2 py-1 max-w-xs break-words truncate"
      onClick={() => setInput(input + suggestion + " ")}
      title={suggestion} // Tooltip for full suggestion
    >
      {suggestion}
    </Button>
  ))}
</div>
      <div className="bg-gray-200 p-1">
        <div className="flex justify-between mb-1">
          <Button
            variant="secondary"
            className="w-10 h-10 md:w-12 md:h-12 text-sm md:text-base font-medium"
            onClick={handleLightbulbClick}
          >
            <Lightbulb className="w-4 h-4 md:w-5 md:h-5" />
          </Button>
          {numberKeys.map((key) => (
            <Button
              key={key}
              variant="secondary"
              className="w-8 h-10 md:w-10 md:h-12 text-sm md:text-base font-medium"
              onClick={() => handleKeyPress(key)}
            >
              {key}
            </Button>
          ))}
        </div>
        {keys.map((row, rowIndex) => (
          <div key={rowIndex} className="flex justify-center mb-1">
            {row.map((key, keyIndex) => (
              <Button
                key={keyIndex}
                variant="secondary"
                className={`m-0.5 ${
                  key === "space"
                    ? "flex-grow"
                    : key === "shift" || key === "backspace" || key === "undo"
                    ? "w-12 md:w-16"
                    : key === "123" || key === "send" || key === "abc"
                    ? "w-16 md:w-20"
                    : "w-8 md:w-10"
                } h-10 md:h-12 text-sm md:text-base font-medium`}
                onClick={() => {
                  if (key === "shift") {
                    setIsUpperCase(!isUpperCase);
                  } else if (key === "123") {
                    setIsSpecialChar(true);
                  } else if (key === "abc") {
                    setIsSpecialChar(false);
                  } else {
                    handleKeyPress(key);
                  }
                }}
              >
                {key === "backspace" ? (
                  <Delete className="w-4 h-4 md:w-5 md:h-5" />
                ) : key === "undo" ? (
                  <Undo2 className="w-4 h-4 md:w-5 md:h-5" />
                ) : key === "shift" ? (
                  <ArrowUp className="w-4 h-4 md:w-5 md:h-5" />
                ) : key === "123" || key === "abc" ? (
                  <Keyboard className="w-4 h-4 md:w-5 md:h-5" />
                ) : (
                  isUpperCase ? key.toUpperCase() : key
                )}
              </Button>
            ))}
          </div>
        ))}
      </div>
    </Card>
  );
}
