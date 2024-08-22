<script>
	import { Router, Route } from "svelte-routing";
	import Home from "./routes/Home.svelte";
	import Session from "./routes/Session.svelte";
  
	export let url = "";
  </script>
  
  <Router {url}>
	<Route path="/" component={Home} />
	<Route path="/session/:id" let:params>
	  <Session id={params.id} />
	</Route>
  </Router>
  
  <style global>
	@tailwind base;
	@tailwind components;
	@tailwind utilities;
  </style>