import { useEffect, useState, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { io } from "socket.io-client";
import LoadingScreen from "./loading_screen";

export default function Narration() {
  const location = useLocation();
  const navigate = useNavigate();

  const { gameId, playerId, name, story: initialStory } = location.state || {};

  const [story, setStory] = useState(initialStory || "");
  const [storyType, setStoryType] = useState("story");
  const [isLoading, setIsLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [currentRound, setCurrentRound] = useState(1);

  const [displayedText, setDisplayedText] = useState("");
  const [allGeneratedText, setAllGeneratedText] = useState("");
  const [sentences, setSentences] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [animationDirection, setAnimationDirection] = useState(1);
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [showCompleteText, setShowCompleteText] = useState(false);
  const [hasContinued, setHasContinued] = useState(false);
  const [socket, setSocket] = useState(null);

  const textBoxRef = useRef(null);

  const totalFrames = 16;
  const frameWidth = 64;

  const handleScroll = () => {
    if (textBoxRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = textBoxRef.current;
      setIsUserScrolling(scrollTop + clientHeight < scrollHeight - 5);
    }
  };

  // Add loading simulation effect
  useEffect(() => {
    if (story) {
      let progress = 0;
      const loadingInterval = setInterval(() => {
        progress += 0.1;
        setLoadingProgress(progress);

        if (progress >= 1) {
          clearInterval(loadingInterval);
          setTimeout(() => {
            setIsLoading(false);
          }, 500);
        }
      }, 100);

      return () => clearInterval(loadingInterval);
    }
  }, [story]);

  // Add function to determine loading type
  const getLoadingType = () => {
    if (storyType === "background") return "sunrise";
    if (storyType === "day") return "sunrise";
    return "nightfall";
  };

  // Socket connection
  useEffect(() => {
    if (!gameId || !playerId) {
      navigate("/");
      return;
    }

    const s = io("http://localhost:5001");
    setSocket(s);

    s.emit("join", { game_id: gameId, player_id: playerId });

    // Handle background story (game start)
    s.on("game_started", (data) => {
      if (data.background_story) {
        setStory(data.background_story);
        setStoryType("background");
        setCurrentRound(1); // Game just started
        setIsLoading(true);
        setLoadingProgress(0);
      }
    });

    // Handle day story (after night phase)
    s.on("day_started", (data) => {
      if (data.story) {
        setStory(data.story);
        setStoryType("day");
        setIsLoading(true);
        setLoadingProgress(0);

        // Get round from game state
        if (data.game_state && data.game_state.round) {
          setCurrentRound(data.game_state.round);
        }
      }
    });

    s.on("player_continue_update", (data) => {
      console.log("Player continue update:", data);
    });

    s.on("all_players_continued", (data) => {
      console.log("All players continued:", data);

      if (data.next_phase === "night") {
        navigate("/night-phase", { state: { gameId, playerId, name } });
      } else if (data.next_phase === "discussion") {
        navigate("/discussion-phase", { state: { gameId, playerId, name } });
      } else {
        // Fallback based on story type
        if (storyType === "background") {
          navigate("/night-phase", { state: { gameId, playerId, name } });
        } else if (storyType === "day") {
          navigate("/discussion-phase", { state: { gameId, playerId, name } });
        } else {
          navigate("/");
        }
      }
    });

    s.on("error", (error) => {
      console.error("Socket error:", error);
      alert(error.msg || "An error occurred");
    });

    return () => s.disconnect();
  }, [gameId, playerId, navigate, storyType, name]);

  // Split story into sentences (only when not loading)
  useEffect(() => {
    if (story && !isLoading) {
      const parts = story
        .split(".")
        .map((s) => s.trim())
        .filter((s) => s.length);
      setSentences(parts);
      setCurrentIndex(0);
      setDisplayedText("");
      setAllGeneratedText("");
      setShowCompleteText(false);
      setIsTyping(false);
      setHasContinued(false);
    }
  }, [story, isLoading]);

  useEffect(() => {
    if (!isUserScrolling && textBoxRef.current) {
      textBoxRef.current.scrollTop = textBoxRef.current.scrollHeight;
    }
  }, [allGeneratedText, isUserScrolling]);

  // Sprite animation effect
  useEffect(() => {
    if (!isTyping) {
      setCurrentFrame(0);
      setAnimationDirection(1);
      return;
    }

    const frameInterval = setInterval(() => {
      setCurrentFrame((prevFrame) => {
        let nextFrame = prevFrame + animationDirection;
        if (nextFrame >= totalFrames - 1) {
          setAnimationDirection(-1);
          return totalFrames - 1;
        } else if (nextFrame <= 0) {
          setAnimationDirection(1);
          return 0;
        }
        return nextFrame;
      });
    }, 350);

    return () => clearInterval(frameInterval);
  }, [isTyping, animationDirection]);

  // Typing effect (only when not loading)
  useEffect(() => {
    if (
      isLoading ||
      sentences.length === 0 ||
      currentIndex >= sentences.length
    ) {
      setIsTyping(false);
      setShowCompleteText(true);
      return;
    }

    const sentence = sentences[currentIndex];
    let i = 0;
    setDisplayedText("");
    setIsTyping(true);

    const interval = setInterval(() => {
      if (i < sentence.length) {
        const char = sentence[i];
        if (char !== undefined) {
          setDisplayedText((prev) => prev + char);
          setAllGeneratedText((prev) => prev + char);
        }
        i++;
      } else {
        clearInterval(interval);
        setIsTyping(false);
        if (!sentence.trim().endsWith(".")) {
          setAllGeneratedText((prev) => prev + ". ");
        } else {
          setAllGeneratedText((prev) => prev + " ");
        }
        setTimeout(() => setCurrentIndex((idx) => idx + 1), 1000);
      }
    }, 50);

    return () => clearInterval(interval);
  }, [currentIndex, sentences, isLoading]);

  // Continue button handler
  const handleContinue = () => {
    if (socket && !hasContinued) {
      socket.emit("player_continue", { game_id: gameId, player_id: playerId });
      setHasContinued(true);
    }
  };

  // Show loading screen while story is being prepared
  if (isLoading && story) {
    return <LoadingScreen type={getLoadingType()} progress={loadingProgress} />;
  }

  // Show waiting state if no story yet
  if (!story) {
    return (
      <div className="flex flex-col h-screen items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 text-white">
        <div className="text-2xl font-medium mb-4">Waiting for story...</div>
        <div className="text-lg text-gray-400">Game: {gameId}</div>
        <div className="text-lg text-gray-400">Player: {name}</div>
      </div>
    );
  }

  // Determine display title based on story type
  const getStoryTitle = () => {
    if (storyType === "background") return "Game Start";
    if (storyType === "day") return `Day ${currentRound}`;
    return "Story";
  };

  return (
    <div className="flex flex-col h-screen items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      <div className="absolute top-6 left-6 text-white text-lg">
        Game: {gameId} | Player: {name}
      </div>
      <div className="absolute top-6 right-6 text-white text-lg capitalize">
        {getStoryTitle()} Story
      </div>

      {/* Day Counter Badge for Day stories */}
      {storyType === "day" && (
        <div className="absolute top-16 left-1/2 transform -translate-x-1/2">
          <div className="bg-blue-500/80 rounded-full px-4 py-2 text-white font-bold">
            Day {currentRound}
          </div>
        </div>
      )}

      <div className="relative mb-8 mt-8">
        <div
          className="w-16 h-16 overflow-hidden"
          style={{
            backgroundImage: `url(/assets/talking-guy.png)`,
            backgroundSize: `${totalFrames * 100}% 100%`,
            backgroundPosition: `-${currentFrame * frameWidth}px 0px`,
            backgroundRepeat: "no-repeat",
            imageRendering: "pixelated",
          }}
        />
      </div>

      <div className="w-3/4 max-w-2xl text-center">
        <div
          ref={textBoxRef}
          onScroll={handleScroll}
          className="text-xl font-medium p-6 rounded-lg bg-black bg-opacity-30 backdrop-blur-sm border border-white border-opacity-20 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent"
          style={{ height: "12rem", minHeight: "12rem" }}
        >
          <div className="text-left">{allGeneratedText}</div>
        </div>
      </div>

      <button
        onClick={handleContinue}
        className={`mt-12 py-2 px-6 rounded-lg font-semibold text-lg transition-all duration-200 hover:scale-105 active:scale-95 ${
          hasContinued
            ? "bg-gray-600 hover:bg-gray-700 text-gray-300 cursor-default"
            : "bg-green-500 hover:bg-green-600 text-white"
        }`}
        disabled={hasContinued}
      >
        {hasContinued ? "Waiting for others..." : "Continue"}
      </button>
    </div>
  );
}
